from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError

from learn_flask.blueprints import get_item_or_404, get_store_or_404, get_tag_or_404
from learn_flask.extensions import db
from learn_flask.models import TagModel
from learn_flask.schemas import MessageSchema, TagAndItemSchema, TagSchema

tag_blp = Blueprint("Tags", "tags", description="Operations on tags")


@tag_blp.route("/stores/<int:store_id>/tags")
class TagsInStore(MethodView):
    @tag_blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = get_store_or_404(store_id)
        return store.tags.all()

    @tag_blp.arguments(TagSchema)
    @tag_blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        get_store_or_404(store_id)
        tag = TagModel(**tag_data, store_id=store_id)
        try:
            db.session.add(tag)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(400, message="This store already has a tag with that name.")

        return tag


@tag_blp.route("/items/<uuid:item_id>/tags/<uuid:tag_id>")
class LinkTagToItem(MethodView):
    @tag_blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = get_item_or_404(item_id)
        tag = get_tag_or_404(tag_id)

        if item.store_id != tag.store_id:
            abort(400, message="Item and tag must belong to the same store.")

        if tag not in item.tags:
            item.tags.append(tag)
            db.session.commit()

        return tag

    @tag_blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = get_item_or_404(item_id)
        tag = get_tag_or_404(tag_id)

        if tag not in item.tags:
            abort(404, message=f"Tag '{tag_id}' is not linked to item '{item_id}'.")

        item.tags.remove(tag)
        db.session.commit()
        return {"message": "Tag removed from item.", "item": item, "tag": tag}


@tag_blp.route("/tags/<uuid:tag_id>")
class Tag(MethodView):
    @tag_blp.response(200, TagSchema)
    def get(self, tag_id):
        return get_tag_or_404(tag_id)

    @tag_blp.response(200, MessageSchema)
    def delete(self, tag_id):
        tag = get_tag_or_404(tag_id)
        if tag.items:
            abort(
                400,
                message="Tag is linked to items. Unlink them before deleting the tag.",
            )

        db.session.delete(tag)
        db.session.commit()
        return {"message": f"Tag '{tag_id}' deleted."}
