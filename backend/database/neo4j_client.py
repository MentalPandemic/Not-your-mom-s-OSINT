from neo4j import GraphDatabase
import os

class Neo4jClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_user_node(self, username, name, email, location, company):
        with self.driver.session() as session:
            session.write_transaction(self._create_user_node, username, name, email, location, company)

    @staticmethod
    def _create_user_node(tx, username, name, email, location, company):
        tx.run("MERGE (u:GitHubUser {username: $username}) "
               "SET u.name = $name, u.email = $email, u.location = $location, u.company = $company",
               username=username, name=name, email=email, location=location, company=company)

    def create_relationship(self, from_node, to_node, rel_type):
        # Generic relationship creator
        pass
