"""Initial database migration

Revision ID: 001_initial
Revises: 
Create Date: 2026-03-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 招标文件文档表
    op.create_table(
        'tender_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('project_overview', sa.Text(), nullable=True),
        sa.Column('technical_requirements', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tender_documents_id'), 'tender_documents', ['id'], unique=False)

    # 投标项目表
    op.create_table(
        'bid_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('tender_document_id', sa.Integer(), nullable=True),
        sa.Column('project_overview', sa.Text(), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('tender_company', sa.String(500), nullable=True),
        sa.Column('tender_contact', sa.String(200), nullable=True),
        sa.Column('tender_phone', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['tender_document_id'], ['tender_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bid_projects_id'), 'bid_projects', ['id'], unique=False)

    # 企业资料表
    op.create_table(
        'enterprise_materials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bid_project_id', sa.Integer(), nullable=True),
        sa.Column('material_type', sa.String(100), nullable=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(1000), nullable=True),
        sa.Column('minio_object_name', sa.String(1000), nullable=True),
        sa.Column('file_url', sa.String(2000), nullable=True),
        sa.Column('issue_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('is_expired', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['bid_project_id'], ['bid_projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enterprise_materials_id'), 'enterprise_materials', ['id'], unique=False)

    # 文档大纲表
    op.create_table(
        'document_outlines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tender_document_id', sa.Integer(), nullable=True),
        sa.Column('bid_project_id', sa.Integer(), nullable=True),
        sa.Column('outline_data', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tender_document_id'], ['tender_documents.id'], ),
        sa.ForeignKeyConstraint(['bid_project_id'], ['bid_projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_outlines_id'), 'document_outlines', ['id'], unique=False)

    # 文档内容表
    op.create_table(
        'document_contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('outline_id', sa.Integer(), nullable=False),
        sa.Column('chapter_path', sa.String(100), nullable=True),
        sa.Column('chapter_title', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_ai_generated', sa.Boolean(), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('generation_model', sa.String(100), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('approval_note', sa.Text(), nullable=True),
        sa.Column('vector_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['outline_id'], ['document_outlines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_contents_id'), 'document_contents', ['id'], unique=False)

    # 用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('hashed_password', sa.String(200), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('company', sa.String(500), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 搜索历史表
    op.create_table(
        'search_histories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('search_type', sa.String(50), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=True),
        sa.Column('results_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_histories_id'), 'search_histories', ['id'], unique=False)

    # 应用配置表
    op.create_table(
        'app_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(100), nullable=False),
        sa.Column('config_value', sa.Text(), nullable=True),
        sa.Column('config_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_app_configs_id'), 'app_configs', ['id'], unique=False)
    op.create_index(op.f('ix_app_configs_config_key'), 'app_configs', ['config_key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_app_configs_config_key'), table_name='app_configs')
    op.drop_index(op.f('ix_app_configs_id'), table_name='app_configs')
    op.drop_table('app_configs')
    op.drop_index(op.f('ix_search_histories_id'), table_name='search_histories')
    op.drop_table('search_histories')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_document_contents_id'), table_name='document_contents')
    op.drop_table('document_contents')
    op.drop_index(op.f('ix_document_outlines_id'), table_name='document_outlines')
    op.drop_table('document_outlines')
    op.drop_index(op.f('ix_enterprise_materials_id'), table_name='enterprise_materials')
    op.drop_table('enterprise_materials')
    op.drop_index(op.f('ix_bid_projects_id'), table_name='bid_projects')
    op.drop_table('bid_projects')
    op.drop_index(op.f('ix_tender_documents_id'), table_name='tender_documents')
    op.drop_table('tender_documents')
