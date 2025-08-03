from __future__ import absolute_import

import datetime
import json
import logging

from sqlalchemy import inspect, and_, or_, desc

from mysql.db_client import DBClient
from mysql.main_db import DatabaseManager

class AmlEvent:
    def __init__(self,  job_id, component_id, sub_component_id, event_code,
                    event_description=None, event_data=None, version=None):
        self.job_id:int = job_id
        self.component_id= component_id
        self.sub_component_id = sub_component_id
        self.event_code = event_code
        self.event_description = event_description
        self.event_data = event_data
        self.version = version

    def addContext_kv(self, key, value):
        self.event_data[key] = value
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'component_id': self.component_id,
            'sub_component_id': self.sub_component_id,
            'event_code': self.event_code,
            'event_description': self.event_description,
            'event_data': self.event_data,
            'version': self.version
        }
    
    def __str__(self):
        return (f"AmlEvent(job_id={self.job_id}, component_id={self.component_id}, "
                f"sub_component_id={self.sub_component_id}, event_code={self.event_code}, "
                f"event_description={self.event_description}, event_data={self.event_data}, "
                f"version={self.version})")

class AmlEventClient(DatabaseManager):
    def __init__(self, db_handle):
        super(AmlEventClient, self).__init__(db_handle)

    @staticmethod
    def _object_as_dict(obj):
        obj_dict = {}
        for column in inspect(obj).mapper.column_attrs:
            key = column.key
            value = getattr(obj, column.key)
            if isinstance(value, datetime.datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            obj_dict[key] = value
        return obj_dict

    def insert_event(self, job_id, component_id, sub_component_id, event_code,
                    event_description=None,event_data=None, version=None):
        AmlEventPool = self._base.classes.aml_event_pool
        with self._session_scope() as session:
            try:
                event = AmlEventPool()
                event.job_id = job_id
                event.component_id = component_id
                event.sub_component_id = sub_component_id
                event.event_code = event_code
                event.event_description = event_description
                event.event_data = json.dumps(event_data or {})
                event.version = version
                event.created_at = datetime.datetime.now()
                event.updated_at = datetime.datetime.now()
                event.version = version
                session.add(event)
                session.commit()
                return job_id if job_id else event.id, ""
            except Exception as e:
                err_msg = "insert event error: {}".format(repr(e))
                logging.error(err_msg)
                return 0, err_msg

    def query_events(self, query_dict=None, query_by_desc=False, limit=None):
        AmlEventPool = self._base.classes.aml_event_pool
        query_dict = query_dict or {}
        with self._session_scope() as session:
            try:
                matched_event_list = []
                filters = []
                for column in AmlEventPool.__table__.columns:
                    if column.name in query_dict and query_dict[column.name] is not None:
                        if column.name in ["created_at", "updated_at"]:
                            filters.append(and_(column > query_dict[column.name]))
                        else:
                            filters.append(and_(column == query_dict[column.name]))
                query = DBClient(session).select(AmlEventPool, filters)
                if query_by_desc:
                    query = query.order_by(desc(AmlEventPool.job_id))
                if limit:
                    query = query.limit(limit)
                for res in query:
                    matched_event_list.append(self._object_as_dict(res))
                return matched_event_list
            except Exception as e:
                logging.error("query event error: {}".format(repr(e)))
                return None

    def update_event(self, id, job_id, **kwargs):
        AmlEventPool = self._base.classes.aml_event_pool
        with self._session_scope() as session:
            try:
                job = session.query(AmlEventPool)\
                        .filter(AmlEventPool.id == id)\
                        .filter(AmlEventPool.job_id == job_id)\
                        .one()
                job.updated_at = datetime.datetime.now()
                for column in AmlEventPool.__table__.columns:
                    if column.name in kwargs and kwargs[column.name] is not None:
                        setattr(job, column.name, kwargs[column.name])
                session.add(job)
                session.commit()
                return True, ""
            except Exception as e:
                err_msg = "update job error: {}".format(repr(e))
                logging.error(err_msg)
                return False, err_msg
            
    def reset_database(self):
        AmlEventPool = self._base.classes.aml_event_pool
        with self._session_scope() as session:
            try:
                session.query(AmlEventPool).delete()
                session.commit()
                print("All job should be deleted")
                return True
            except Exception as e:
                err_msg = f"fail to delete {e}"
                print(err_msg)
                return False
