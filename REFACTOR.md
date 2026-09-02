# What I changed, and why

This file explains the `layered-architecture` branch. It is written for the
presentation: every change is shown as **before → after**, with the file it
lives in, the reason I made it, and the option I did **not** pick.

The branch is a refactor, not a feature branch. Almost no new behaviour was
added. The same routes do the same thing. What changed is **where the code
lives** and **who is allowed to know about what**.

To see the whole thing at once:

```bash
git diff main..layered-architecture
```

---

## 0. The one rule

Everything below follows from one rule:

```
resources/  →  services/  →  models/
  HTTP          rules         tables
```

The arrow only points right. `resources/` may call `services/`. `services/`
may call `models/`. Nothing ever points back left.

In practice this means: **a service is not allowed to know that HTTP exists.**
No `request`, no `abort()`, no `jsonify`, no `current_app`.

Why this matters: the rules of my app (what makes a username taken, when a tag
may be deleted) are the valuable part. Web frameworks change. If the rules are
glued to Flask, they die with Flask. If they are plain Python, I can call them
from a CLI, a test, a background worker, or a different framework tomorrow.

You can check the rule with one command:

```bash
grep -rnE "^(from|import) (flask|flask_[a-z_]+)" src/learn_flask --include="*.py"
```

Every line it prints is in `__init__.py`, `extensions.py`, `main.py`, or
`resources/`. Nothing in `services/`, `errors.py`, `config.py` or
`notifications.py` appears.

> **A small honest note for the presentation.** Do not run the shorter
> `grep -rl flask src/` — it "fails" on every file, because the *package itself*
> is called `learn_flask`, so the word `flask` appears in every import line
> (`from learn_flask.errors import ...`). The `^(from|import)` version above is
> the honest check. Better to point this out yourself than to have someone find
> it. It is also a good argument for not naming a package after its framework.

---

## 1. `blueprints/` → `resources/` + `services/`

This is the main change. Everything else supports it.

### Before

`src/learn_flask/blueprints/store.py` on `main`. The route function does five
different jobs:

```python
@store_blp.route("/")
class StoreList(MethodView):
    @store_blp.arguments(StoreSchema)
    @store_blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)          # 1. builds the row
        try:
            db.session.add(store)                 # 2. talks to the database
            db.session.commit()                   # 3. controls the transaction
        except IntegrityError:
            db.session.rollback()                 # 4. handles the failure
            abort(400, message="A store with this name already exists.")
                                                  # 5. picks the HTTP status
        return store
```

### After

`src/learn_flask/resources/store.py` — the route now does **one** job: take the
validated input, call one method, return the result.

```python
@store_blp.route("/")
class StoreList(MethodView):
    @store_blp.arguments(StoreSchema)
    @store_blp.response(201, StoreSchema)
    def post(self, store_data):
        return services().stores.create(store_data)
```

`src/learn_flask/services/store_service.py` — the actual work, with no Flask
anywhere in the file:

```python
class StoreService:
    def __init__(self, session):
        self.session = session

    def create(self, data):
        store = StoreModel(**data)
        self.session.add(store)
        self._commit()
        return store

    def _commit(self):
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ConflictError(TAKEN) from None
```

### Why

The `post` on `main` mixes two very different kinds of knowledge: *"a store
name must be unique"* (a rule about my business) and *"a duplicate is HTTP
409"* (a fact about the web). These change for different reasons and should not
live in the same function.

Three concrete wins:

1. **The rule can be tested without a web server.** `StoreService(session)` is
   a plain object. No app, no test client, no request context.
2. **A second caller is free.** If I add a CLI command or an admin script, it
   calls `stores.create(...)` and gets the same duplicate check for free. On
   `main` I would have to copy the whole `try/except` block.
3. **A route that is one line long is a route with nowhere to hide a bug.**

### What I did not do, and why

- **I did not just move the code into loose functions in a `helpers.py`.** That
  is what `main` already had — see `blueprints/__init__.py` on `main`, with
  `get_store_or_404`, `get_item_or_404`, and friends. It works, but those
  functions reach for the global `db.session` on their own. That is a hidden
  input: you cannot see it in the signature, and you cannot swap it. A class
  that takes `session` in `__init__` makes the dependency visible and
  replaceable. That is dependency injection, and it is the whole reason for the
  class.
- **I did not rename it to `controllers/`.** `resources/` is the flask-smorest
  word for a `MethodView` class, so the folder name matches the library the
  project actually uses.

---

## 2. One place where objects are built: `build_services()`

### Before

There was no such place. Every module imported `db` from `extensions` and used
the global session directly.

### After

`src/learn_flask/services/__init__.py:31`:

```python
@dataclass(frozen=True)
class Services:
    users: UserService
    health: HealthService
    stores: StoreService
    items: ItemService
    tags: TagService


def build_services(session, email_sender):
    stores = StoreService(session)
    items = ItemService(session, stores)
    return Services(
        users=UserService(session, email_sender),
        health=HealthService(session),
        stores=stores,
        items=items,
        tags=TagService(session, stores, items),
    )
```

Called once at startup, in `src/learn_flask/__init__.py:33`:

```python
def _init_services(app):
    queue = _build_queue(app.config)
    email_sender = build_email_sender(app.config, queue)
    app.extensions["services"] = build_services(db.session, email_sender)
```

And read per request in `src/learn_flask/resources/__init__.py`:

```python
def services():
    # Looked up per request, not imported: the services belong to one app.
    return current_app.extensions["services"]
```

### Why

This is the **composition root**: the single spot in the program where
"which concrete class do I actually use" is decided. Everywhere else only
speaks to what it was handed.

Look at `TagService(session, stores, items)`. Tag rules genuinely need stores
and items — "you cannot tag an item from another store" needs both. Because
that is written out in one place, the dependency is visible. On `main` the same
relationship existed too, but it was invisible: it was hidden inside function
bodies that imported whatever they liked.

Note also that `stores` and `items` are built **once and shared**, not built
twice. Same object, two owners.

### What I did not do, and why

- **I did not use a DI container library** (`dependency-injector`, `punq`,
  etc.). For five services, a 10-line function is clearer than a framework, and
  it needs no new dependency. Containers pay off when wiring is dynamic; mine is
  fixed and fits on one screen.
- **I did not store the services in a module-level global.** They are attached
  to the app (`app.extensions["services"]`). Two apps in one process — which is
  exactly what tests do — then get their own set instead of fighting over one.
- **`Services` is a frozen dataclass, not a dict.** `services().stores` is
  checked by the editor and autocompletes. `services()["stores"]` is a typo
  waiting to happen at runtime.

---

## 3. `abort()` → typed errors + one handler

### Before

Services did not exist, so route code called flask-smorest's `abort()` directly,
and the HTTP status was chosen deep inside the logic:

```python
# main, blueprints/user.py
def reject_if_taken(name, email):
    if db.session.scalar(db.select(UserModel).where(UserModel.name == name)):
        abort(400, message=f"The username '{name}' already exists. ...")
```

### After

`src/learn_flask/errors.py` — a small family of exceptions, each carrying its
own status code:

```python
class StoreAPIError(Exception):
    status_code = 500
    message = "Something went wrong."


class NotFoundError(StoreAPIError):
    status_code = 404


class ConflictError(StoreAPIError):
    status_code = 409


class BusinessRuleError(StoreAPIError):
    """Well-formed request that breaks a rule marshmallow cannot check."""
    status_code = 422
```

The service raises a plain Python exception, no Flask involved
(`services/user_service.py`):

```python
raise ConflictError(f"The username '{name}' already exists. Please pick another one.")
```

And one handler, registered once in `errors.py:53`, turns any of them into JSON:

```python
def register_error_handlers(app):
    # The shape matches flask-smorest's own errors, so clients parse one format.
    @app.errorhandler(StoreAPIError)
    def handle_store_api_error(error):
        return {
            "code": error.status_code,
            "status": HTTP_STATUS_CODES.get(error.status_code, "Unknown Error"),
            "message": error.message,
        }, error.status_code
```

Because Flask matches error handlers by base class, registering the parent
`StoreAPIError` catches all six children. Adding a seventh error type needs no
change here at all.

### Why

`abort()` is a Flask function. If a service called it, the service would know
about HTTP, and rule 0 would be broken on line one. Raising an exception is how
plain Python reports a problem, and the exception is the natural place to carry
"which status code does this mean".

**Two status codes actually got fixed along the way**, and this is worth saying
out loud in the presentation because it shows the refactor found real bugs:

| Case | `main` | now | why |
| --- | --- | --- | --- |
| Duplicate store or username | 400 | **409 Conflict** | 400 means "your request was malformed". The request was perfectly well formed — it just lost a race with an existing row. |
| Deleting a tag that is still linked to items | 400 | **422 Unprocessable** | The JSON parsed fine and every field was valid. What failed was a rule that no schema can express. |

### What I did not do, and why

- **I did not give every error type its own handler.** One handler on the base
  class is enough, and it guarantees every error in the app comes out in the
  same shape.
- **I did not invent my own JSON error format.** I copied flask-smorest's
  (`code` / `status` / `message`), so a client sees one format whether the error
  came from marshmallow validation or from my service layer. Mixed error shapes
  in one API is a quiet cruelty to whoever consumes it.
- **I named it `ForbiddenError`, not `PermissionError`** — Python already has a
  builtin called `PermissionError`, and shadowing a builtin is how you get an
  exception that catches the wrong thing at 2am.

---

## 4. Email: one function → a Strategy

This is the one place where a named design pattern really earns its place.

### Before

`src/learn_flask/email.py` on `main` — one function that hard-codes Brevo,
reads the environment itself, and decides on its own whether to queue:

```python
def send_welcome_email(name, email):
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        log.info("BREVO_API_KEY not set -- skipping welcome email to %s", email)
        return
    payload = { ...brevo's exact json shape... }
    httpx.post(BREVO_ENDPOINT, json=payload, ...)


def enqueue_welcome_email(name, email):
    queue = current_app.extensions.get("rq_queue")
    if queue is None:
        send_welcome_email(name, email)     # falls back to inline
        return
    queue.enqueue(send_welcome_email, name, email)
```

Three problems. The signup path is stuck with Brevo forever. `enqueue_...`
touches `current_app`, so it cannot run outside a request. And there is no way
to check "did we send the email?" in a test without hitting the real network.

### After

`src/learn_flask/notifications.py`. First, one small interface:

```python
class EmailSender(ABC):
    @abstractmethod
    def send(self, email: Email) -> None:
        """Must not raise. A failed welcome email is not a failed signup."""
```

Then two ways to satisfy it — `BrevoSender` (real network call) and
`ConsoleSender` (prints it to the log). Then a third one that is the interesting
part, because it implements the same interface *and takes one*:

```python
class QueuedSender(EmailSender):
    """Wraps any sender and hands the work to a background worker instead."""

    def __init__(self, inner, queue):
        self._inner = inner
        self._queue = queue

    def send(self, email):
        try:
            self._queue.enqueue(deliver, self._inner, email)
        except Exception as exc:
            # Redis being down must not fail a signup that already worked.
            log.warning("Could not queue the email to %s: %s", email.to_email, exc)
            self._inner.send(email)
```

And the choice is made once, from config:

```python
BACKENDS = {
    "brevo": lambda c: BrevoSender(c["BREVO_API_KEY"], c["MAIL_FROM_EMAIL"], c["MAIL_FROM_NAME"]),
    "console": lambda c: ConsoleSender(),
}


def build_email_sender(config, queue=None):
    build = BACKENDS.get(config["EMAIL_BACKEND"])
    if build is None:
        raise RuntimeError(f"Unknown EMAIL_BACKEND {config['EMAIL_BACKEND']!r}. ...")
    sender = build(config)
    return QueuedSender(sender, queue) if queue is not None else sender
```

`UserService` now knows nothing about any of this:

```python
self.email_sender.send(welcome_email(user.name, user.email))
```

### Why

Signup should mean "create the user, then tell somebody". *How* it tells
somebody — Brevo, the console, later, now — is a deployment decision, not a
business rule. Putting it behind an interface is what lets the rule stop caring.

Two details worth pointing at during the presentation:

- **`QueuedSender` wraps a sender instead of replacing one.** Queueing is a
  *delivery* concern that is independent of *which provider*. Because it wraps,
  I get all four combinations (Brevo now / Brevo queued / console now / console
  queued) out of three small classes instead of writing four. This is the
  decorator shape: same interface in, same interface out, one behaviour added.
- **`BrevoSender.__init__` stores strings, not an `httpx.Client`.** rq *pickles*
  this object to send it to the worker process, and an open socket does not
  survive pickling. That comment is in the code for a reason; it is a real bug I
  designed around, not a style choice.

### What I did not do, and why

- **I did not use `if/elif` on a provider name inside the send function.** That
  is the same code with the branch moved: every new provider still means editing
  the one function everyone shares. With a dict of builders, a new provider is a
  new class plus one dict entry, and nothing existing is touched.
- **`BACKENDS` raises on an unknown name** instead of silently falling back to
  console. A typo in `EMAIL_BACKEND` should fail loudly at startup, not quietly
  stop sending mail in production for a week.

> **Gap to be honest about.** `CLAUDE.md` mentions a `NullSender` and a
> `RecordingSender`. They are **not in the code** right now
> (`grep -rn "NullSender" src/` finds nothing). The strategy is what makes such
> a test double a three-line class, but until tests exist, that benefit is a
> claim, not a demonstration. If asked "what would you do next?", this plus
> pytest is the honest answer.

---

## 5. Config: scattered `os.getenv` → one typed `Settings`

### Before

`create_app()` on `main` was ~60 lines of `app.config[...] = ...`, mixed in with
`os.getenv` calls and their defaults:

```python
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY", "dev-only-secret-not-for-production-use-32b"
)
```

Every value is a string. A typo in a variable name silently gives you the
default. And the dev-only JWT secret — which is committed to git — would happily
be used in production.

### After

`src/learn_flask/config.py`, one `Settings` class on **pydantic-settings**:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    APP_ENV: str = "development"

    # Flask-SQLAlchemy wants SQLALCHEMY_DATABASE_URI; the environment variable
    # everyone writes is DATABASE_URL. The alias bridges the two.
    SQLALCHEMY_DATABASE_URI: str = Field(default="", alias="DATABASE_URL")

    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=15)
```

and one validator that runs after everything is loaded (`config.py:61`):

```python
@model_validator(mode="after")
def apply_environment_rules(self):
    production = self.APP_ENV == "production"

    if production:
        # The dev fallbacks below are committed to git, so anyone could
        # forge a token. Crash rather than boot with them on a real server.
        missing = [name for name, value in (
            ("DATABASE_URL", self.SQLALCHEMY_DATABASE_URI),
            ("JWT_SECRET_KEY", self.JWT_SECRET_KEY),
        ) if not value]
        if missing:
            raise ValueError("Refusing to start in production without: " + ", ".join(missing))
    else:
        self.SQLALCHEMY_DATABASE_URI = self.SQLALCHEMY_DATABASE_URI or DEV_DATABASE
        self.JWT_SECRET_KEY = self.JWT_SECRET_KEY or DEV_JWT_SECRET

    self.DEBUG = not production

    # No Brevo key means print the email instead of sending it, so a fresh
    # clone runs with nothing to set up.
    if self.EMAIL_BACKEND is None:
        self.EMAIL_BACKEND = "brevo" if self.BREVO_API_KEY else "console"

    return self
```

`create_app()` is now one line for all of it:

```python
app.config.from_object(config or Settings())
```

### Why

- **Types are real.** `JWT_ACCESS_TOKEN_EXPIRES: timedelta` and
  `WEB_PORT: int` are parsed and validated. An unparseable value fails at
  startup with a clear message, instead of becoming a confusing `TypeError` on
  a random request three hours later.
- **A bad production deploy cannot start.** This is the security win, and it is
  the one to say out loud. The old code would run with a secret key that is
  sitting in the public git history. The new code refuses to boot.
- **`create_app()` got its shape back.** It went from ~120 lines to a readable
  list of five steps: init extensions, init services, init jwt, register error
  handlers, register blueprints.
- **`config=None` parameter.** `create_app(SomeTestSettings())` lets a test
  override everything without touching the environment.

### What I did not do, and why

- **I did not use the classic `class DevConfig / class ProdConfig` pattern**
  from most Flask tutorials. That pattern needs inheritance plus a lookup dict
  plus an `if` on an env var. `pydantic-settings` gives me the same thing with
  one class, and adds validation and type parsing that the class-per-env pattern
  never had.
- **I did not keep raw `os.getenv` calls anywhere.** The point is that there is
  exactly one file to read to know every setting this app has.
- **I did not make `Settings` a module-level singleton** (`settings = Settings()`
  at import time). It is created inside `create_app()` instead. See §7 — this is
  a place where I deliberately went against my own other project.

---

## 6. `extensions.py` and the app factory

### Before

Extensions were created *inside* `create_app`, bound to that app forever:

```python
db.init_app(app)
migrate = Migrate(app, db)   # local variable, thrown away
jwt = JWTManager(app)        # local variable, thrown away
```

### After

`src/learn_flask/extensions.py` — built empty, attached later:

```python
# Built empty here and attached to an app later with init_app(), so create_app()
# can run more than once in a single process.
db = SQLAlchemy(model_class=Base)
migrate = Migrate()
jwt = JWTManager()
```

```python
db.init_app(app)
migrate.init_app(app, db)
```

### Why

`Migrate(app, db)` binds at construction. `Migrate()` + `.init_app(app)` does
not, so the same extension objects can serve a second app — which is what
happens the moment you write a test that builds a fresh app per test. This is
the standard Flask idiom and the whole reason `init_app` exists.

One deliberate exception, and the comment says so in `__init__.py`:

```python
def _register_blueprints(app):
    # Api() is per-app, not in extensions.py: a shared one would collect
    # duplicate paths every time create_app() ran again.
    api = Api(app)
```

`Api` accumulates registered routes. Sharing one across apps would build an
OpenAPI document with every path listed twice. So it stays local on purpose. Be
ready for the question "why is this one different?" — the answer is that the
rule is *"don't share mutable state across apps"*, and `init_app` is just the
usual way to obey it, not the rule itself.

---

## 7. What I took from `agens`, and what I refused to take

`agens` is my other Python project (`~/new_world/python/agens`). Its structure
is more advanced than this one, which makes it a useful source — and a useful
temptation to resist. Copying structure you do not need is how projects get
heavy.

### Taken

| From agens | Where it landed here | Why it fit |
| --- | --- | --- |
| `config/settings.py` — pydantic-settings `BaseSettings` with typed fields and validators | `src/learn_flask/config.py` | Same real problem: many settings, from `.env`, that must be typed and must fail loudly when wrong. |
| `core/tool_interface.py` — an ABC everything else is written against | `EmailSender` in `notifications.py` | Same shape: one contract, several concrete implementations, chosen at startup. |
| `agent/factory.py` — one function that builds everything and hands it over | `build_services()` in `services/__init__.py` | Same job: a single composition root, so nothing else has to know which concrete class it is using. |
| A `services/` folder as the home of application logic | `services/` | Same idea, different scale. |

### Refused

| In agens | Not here | Why not |
| --- | --- | --- |
| `db/repository.py` — a repository module wrapping every query | no repository layer | SQLAlchemy's `Session` **already is** a repository plus a unit of work. Wrapping it adds a layer with no behaviour: `def get(id): return session.get(Model, id)`. agens needs its own layer more because it is `async` and mixes concerns; this app does not. Knowing when *not* to add a pattern is the point. |
| `core/registry.py` — a `ToolRegistry` with `register()` / `get()` | plain `BACKENDS` dict in `notifications.py` | A registry earns its place when things register themselves dynamically at runtime, like agens's 15 tools. I have two email backends, both known at import time. A dict is a registry that has not been over-dressed. |
| `settings` as a module-level singleton, imported everywhere (`from config.settings import settings`) | `Settings()` is created in `create_app()` and passed in | A global singleton is read at import time, which means a test cannot change it without patching modules. Flask already has a per-app place for config, and using it means `create_app(TestSettings())` just works. **This is a deliberate disagreement with my own other project** — good to be able to defend it. |
| `config/config_manager.py`, `config/runtime.py`, `config/bootstrap.py`, `config/workspace.py` | one `config.py` | agens is a desktop/CLI app: it must create user directories, manage writable runtime files, and merge several config sources. A containerised web API reads env vars and starts. Copying that machinery would be pure cost. |
| `llm/errors.py` — rich errors carrying `is_transient`, `retry_after`, `is_auth_error` | six small subclasses carrying `status_code` | agens retries and rotates API keys, so its errors must carry *decision data*. My handler asks one question: what status code do I return? So one attribute is exactly right. Same idea, sized to the job. |
| `app_bootstrap.py` — a startup lifecycle module | nothing | Flask's app factory already is that. |

The honest one-line version, for the presentation:

> I copied from agens where the two projects have the same problem, and refused
> to copy where agens's problem is bigger than mine.

---

## 8. Deliberately skipped, with reasons

| Step | Status | Reason |
| --- | --- | --- |
| Repository layer | skipped on purpose | See §7. `Session` already does it. |
| Orders feature | skipped | This branch is about structure, not feature count. Another route proves nothing new. |
| pytest tests | skipped, **the real gap** | This is the weakest point of the branch, and worth admitting before someone asks. The architecture was built *so that* things are testable — services take a session, email hides behind an interface — but with no tests, that is an argument rather than a proof. |
| README, CI, pagination, rate limit | not started | Next up. |

---

## 9. The 60-second version

If there is only time for one slide:

1. **Routes went from doing five jobs to doing one.** They read the request and
   call one method. Every route is now one to three lines.
2. **Business rules moved into service classes that cannot see Flask.** That is
   enforceable and provable with one `grep`.
3. **Errors became typed exceptions with one handler.** The refactor found two
   wrong status codes on the way (400 → 409, 400 → 422).
4. **Email hides behind an interface**, so signup no longer knows what Brevo is,
   and queueing is a wrapper rather than a fork in the code.
5. **Config became one validated class** that refuses to start in production
   with the git-committed dev secret.
6. **I skipped the repository layer on purpose** — and that decision is the part
   of this branch I would most like to be asked about.
