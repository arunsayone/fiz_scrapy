import settings

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.automap import automap_base


class FizScrapyPipeline(object):

    def __init__(self):
        """
        Initializes database connection and sessionmaker.
        Creates deals table.
        """
        print '.... Inside Init .....'
        Base = automap_base()

        # engine, suppose it has two tables 'user' and 'address' set up
        engine = create_engine(URL(**settings.DATABASE))

        # reflect the tables
        Base.prepare(engine, reflect=True)

        # from sqlalchemy import inspect
        # inspector = inspect(engine)
        #
        # for table_name in inspector.get_table_names():
        #     print 'table_name_____\t', table_name
        #     for column in inspector.get_columns(table_name):
        #         print "Column: %s" % column['name']
        #         pass

        # mapped classes are now created with names by default
        # matching that of the table name.
        Provider = Base.classes.core_provider
        ProviderExtraData = Base.classes.core_providerextradata
        # Address = Base.classes.address
        self.session = Session(engine)

        providers = self.session.query(Provider).all()
        # for provider in providers:
        #     print 'Provider id...\t', provider.id
        #     print 'Name.....\n\n', provider.name

        ExtraData = self.session.query(ProviderExtraData).all()

        # for column in inspector.get_columns(ProviderExtraData):
        #     print "Column: %s" % column['name']

        for data in ExtraData:
            for provider in providers:
                if data.provider_id == provider.id:
                    print 'Provider Name.....\n\n', provider.name
                    print 'Data....\n\n', data.data
                    provider_api = provider.api_client()
                    print 'provider_api....\n\n', provider_api

    def process_item(self, item, spider):
        print '++++++ Inside process item +++++++'
        print '\n\n', item, '\n\n'
        return item
