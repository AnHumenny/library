import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging.config import fileConfig
from sqlalchemy import engine_from_config, QueuePool
from alembic import context
from shemas.database import DUser
from dotenv import load_dotenv
load_dotenv()

config = context.config

# Настройка логирования
fileConfig(config.config_file_name)

# Добавьте URL для подключения к базе данных
config.set_main_option('sqlalchemy.url', f"mysql+pymysql:/{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
                                   f"@{os.getenv('DB_HOST')}/{os.getenv('DB_DATABASE')}")

# Добавьте вашу базу моделей для автоматического обнаружения изменений
target_metadata = DUser.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=QueuePool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
