from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class GitHubUser(Base):
    __tablename__ = 'github_users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    real_name = Column(String)
    email = Column(String)
    location = Column(String)
    company = Column(String)
    follower_count = Column(Integer)
    created_date = Column(DateTime)
    
    repositories = relationship("GitHubRepository", back_populates="user")

class GitHubRepository(Base):
    __tablename__ = 'github_repositories'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('github_users.id'))
    repo_name = Column(String, nullable=False)
    description = Column(Text)
    language = Column(String)
    stars = Column(Integer)
    forks = Column(Integer)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    
    user = relationship("GitHubUser", back_populates="repositories")
    commits = relationship("GitHubCommit", back_populates="repository")

class GitHubCommit(Base):
    __tablename__ = 'github_commits'
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey('github_repositories.id'))
    author_name = Column(String)
    author_email = Column(String)
    commit_hash = Column(String)
    commit_message = Column(Text)
    commit_date = Column(DateTime)
    
    repository = relationship("GitHubRepository", back_populates="commits")

class GitHubOrganization(Base):
    __tablename__ = 'github_organizations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('github_users.id'))
    org_name = Column(String)
    org_role = Column(String)
    org_url = Column(String)

class DiscoveredEmail(Base):
    __tablename__ = 'discovered_emails'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    source = Column(String) # github_profile, github_commit, etc.
    confidence = Column(String)

class CredentialWarning(Base):
    __tablename__ = 'credential_warnings'
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey('github_repositories.id'))
    file_path = Column(String)
    credential_type = Column(String)
    discovered_date = Column(DateTime)
