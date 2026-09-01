from flask.views import MethodView
from flask_smorest import Blueprint

from learn_flask.resources import services
from learn_flask.schemas import (
    MessageSchema,
    TagAndItemSchema,
    TagSchema,
    TagUpdateSchema,
)

tag_blp = Blueprint("Tags", "tags", description="Operations on tags")


@tag_blp.route("/tags")
class TagList(MethodView):
    @tag_blp.response(200, TagSchema(many=True))
    def get(self):
        return services().tags.list_all()


@tag_blp.route("/stores/<int:store_id>/tags")
class TagsInStore(MethodView):
    @tag_blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        return services().tags.list_for_store(store_id)

    @tag_blp.arguments(TagSchema)
    @tag_blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        return services().tags.create(store_id, tag_data)


@tag_blp.route("/items/<uuid:item_id>/tags/<uuid:tag_id>")
class LinkTagToItem(MethodView):
    @tag_blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        return services().tags.link_to_item(item_id, tag_id)

    @tag_blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item, tag = services().tags.unlink_from_item(item_id, tag_id)
        return {"message": "Tag removed from item.", "item": item, "tag": tag}


@tag_blp.route("/tags/<uuid:tag_id>")
class Tag(MethodView):
    @tag_blp.response(200, TagSchema)
    def get(self, tag_id):
        return services().tags.get(tag_id)

    @tag_blp.arguments(TagUpdateSchema)
    @tag_blp.response(200, TagSchema)
    def patch(self, tag_data, tag_id):
        return services().tags.update(tag_id, tag_data)

    @tag_blp.response(200, MessageSchema)
    def delete(self, tag_id):
        services().tags.delete(tag_id)
        return {"message": f"Tag '{tag_id}' deleted."}
