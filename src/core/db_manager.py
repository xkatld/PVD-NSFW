from peewee import SqliteDatabase, Model, CharField, TextField, fn
import json

db = SqliteDatabase(None)

class BaseModel(Model):
    class Meta:
        database = db

class Video(BaseModel):
    id = CharField(primary_key=True)
    title = CharField()
    labels = TextField()
    file_name = CharField(null=True)

class DbManager:
    def __init__(self, db_path):
        db.init(db_path)
        db.connect()
        db.create_tables([Video])

    def save_video(self, video_id, info):
        labels_json = json.dumps(info.get("labels", []), ensure_ascii=False)
        Video.insert(
            id=str(video_id),
            title=info.get("title"),
            labels=labels_json,
            file_name=info.get("file_name")
        ).on_conflict_replace().execute()

    def get_all_metadata(self):
        metadata = {}
        for video in Video.select():
            metadata[video.id] = {
                "id": video.id,
                "title": video.title,
                "labels": json.loads(video.labels) if video.labels else [],
                "file_name": video.file_name
            }
        return metadata

    def get_success_videos(self):
        videos = []
        query = Video.select().where(Video.file_name.is_null(False))
        for video in query:
            videos.append({
                "id": video.id,
                "title": video.title,
                "labels": json.loads(video.labels) if video.labels else [],
                "file_name": video.file_name
            })
        return videos

    def get_random_video(self):
        video = Video.select().where(Video.file_name.is_null(False)).order_by(fn.Random()).first()
        if video:
            return {
                "id": video.id,
                "title": video.title,
                "labels": json.loads(video.labels) if video.labels else [],
                "file_name": video.file_name
            }
        return None

    def get_stats(self):
        total = Video.select().count()
        success = Video.select().where(Video.file_name.is_null(False)).count()
        return total, success
