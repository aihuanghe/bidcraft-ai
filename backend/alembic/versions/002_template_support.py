"""Add template support tables

Revision ID: 002_template_support
Revises: 001_initial
Create Date: 2026-03-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_template_support'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 扩展招标文件表，添加模板字段
    op.add_column('tender_documents', sa.Column('has_format_template', sa.Boolean(), nullable=True))
    op.add_column('tender_documents', sa.Column('format_template_chapter', sa.String(100), nullable=True))
    op.add_column('tender_documents', sa.Column('extracted_template_id', sa.Integer(), nullable=True))
    
    # 扩展投标项目表，添加模板字段
    op.add_column('bid_projects', sa.Column('template_id', sa.Integer(), nullable=True))
    op.add_column('bid_projects', sa.Column('template_source', sa.String(20), nullable=True))
    op.add_column('bid_projects', sa.Column('outline_json', sa.JSON(), nullable=True))
    
    # 创建提取的模板表
    op.create_table(
        'extracted_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_doc_id', sa.Integer(), nullable=True),
        sa.Column('template_type', sa.String(20), nullable=True),
        sa.Column('name', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('structure_json', sa.JSON(), nullable=True),
        sa.Column('style_rules', sa.JSON(), nullable=True),
        sa.Column('original_snippets', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_doc_id'], ['tender_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_extracted_templates_id'), 'extracted_templates', ['id'], unique=False)
    
    # 创建模板偏离表
    op.create_table(
        'template_deviations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bid_project_id', sa.Integer(), nullable=False),
        sa.Column('deviation_type', sa.String(50), nullable=True),
        sa.Column('tender_requirement', sa.Text(), nullable=True),
        sa.Column('bid_response', sa.Text(), nullable=True),
        sa.Column('deviation_status', sa.String(20), nullable=True),
        sa.Column('chapter_path', sa.String(100), nullable=True),
        sa.Column('chapter_title', sa.String(500), nullable=True),
        sa.Column('is_confirmed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bid_project_id'], ['bid_projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_deviations_id'), 'template_deviations', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_template_deviations_id'), table_name='template_deviations')
    op.drop_table('template_deviations')
    op.drop_index(op.f('ix_extracted_templates_id'), table_name='extracted_templates')
    op.drop_table('extracted_templates')
    op.drop_column('bid_projects', 'outline_json')
    op.drop_column('bid_projects', 'template_source')
    op.drop_column('bid_projects', 'template_id')
    op.drop_column('tender_documents', 'extracted_template_id')
    op.drop_column('tender_documents', 'format_template_chapter')
    op.drop_column('tender_documents', 'has_format_template')