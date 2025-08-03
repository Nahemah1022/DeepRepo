from __future__ import absolute_import


class DBClient(object):
    def __init__(self, session):
        self.session = session

    def select(self, cls, filters=None, order_by=None, offset=None, limit=None, join=None):
        if filters is None:
            filters = []
        if not isinstance(filters, list):
            filters = [filters]

        query = self.session.query(cls).filter(*filters)
        if order_by is not None:
            query = query.order_by(order_by)
        if join is not None:
            query = query.join(join)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query
    


            
