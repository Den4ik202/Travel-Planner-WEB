from flask_restful import reqparse, abort, Resource
from flask import jsonify
from . import db_session
from data.routs import Route

parser = reqparse.RequestParser()
parser.add_argument('path', required=True)
parser.add_argument('distance', required=True)
parser.add_argument('coordinate_places', required=True)
parser.add_argument('full_adress_places', required=True)
parser.add_argument('enicoding_image', required=True)
parser.add_argument('user_id', required=True)

def abort_if_rout_not_found(rout_id):
    session = db_session.create_session()
    routs = session.query(Route).get(rout_id)
    if not routs:
        abort(404, message=f"Rout {rout_id} not found")


class RoutsResource(Resource):
    def get(self, rout_id):
        abort_if_rout_not_found(rout_id)
        session = db_session.create_session()
        routs = session.query(Route).get(rout_id)
        return jsonify({'routs': routs.to_dict(
            only=('id', 'path', 'distance', 'coordinate_places', 'full_adress_places', 'enicoding_image', 'user_id'))})

    def delete(self, rout_id):
        abort_if_rout_not_found(rout_id)
        session = db_session.create_session()
        routs = session.query(Route).get(rout_id)
        session.delete(routs)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, rout_id):
        args = parser.parse_args()
        db_sess = db_session.create_session()
        routs = db_sess.query(Route).filter(Route.id == rout_id).first()

        routs.path=args['path']
        routs.distance=args['distance']
        routs.coordinate_places=args['coordinat_places']
        routs.full_adress_places=args['full_adress_places']
        routs.enicoding_image=args['enicoding_image']
        routs.user_id=args['user_id']

        db_sess.commit()
        return jsonify({'id': routs.id})


class RoutsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        routs = session.query(Route).all()
        return jsonify({'routs': [item.to_dict(
            only=('id', 'path', 'distance', 'coordinate_places', 'full_adress_places', 'enicoding_image', 'user_id')) for item in routs]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        routs = Route(
            path=args['path'],
            distance=args['distance'],
            coordinate_places=args['coordinate_places'],
            full_adress_places=args['full_adress_places'],
            enicoding_image=args['enicoding_image'],
            user_id=args['user_id']
        )
        session.add(routs)
        session.commit()
        return jsonify({'id': routs.id})
