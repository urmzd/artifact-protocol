Create SQLAlchemy ORM models for a content management system.

Include:
- Base setup with declarative_base, engine, session
- Models: User, Article, Category, Tag, Comment, Media, Permission, AuditLog
- Relationships: articles have authors, categories, tags (M2M), comments; users have roles and permissions
- Query helpers: get_published_articles, search_articles, get_user_activity, get_popular_tags
- Alembic migration helpers: create initial tables, add indexes
