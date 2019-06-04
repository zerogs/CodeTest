from app import app
from views import db
from test_daemon import daemon_start


if __name__ == '__main__':
    db.bind(**app.config['PONY'])
    db.generate_mapping(create_tables=True)
    #create_admin()
    app.run()
    daemon_start()

