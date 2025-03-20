import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

with open('/app/config/storage_app_conf.yaml', 'r') as file:
        config = yaml.safe_load(file)

engine = create_engine(f"mysql://{config['datastore']['user']}:{config['datastore']['password']}@{config['datastore']['hostname']}:{config['datastore']['port']}/{config['datastore']['db']}")
#engine = create_engine("sqlite:///test.db")
def make_session():
        return sessionmaker(bind=engine)()