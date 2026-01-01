// Neo4j initialization script for OSINT Platform
// This script sets up the graph database schema

// Create constraints for uniqueness
CREATE CONSTRAINT identity_unique IF NOT EXISTS FOR (n:Identity) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT email_unique IF NOT EXISTS FOR (n:Email) REQUIRE n.address IS UNIQUE;
CREATE CONSTRAINT phone_unique IF NOT EXISTS FOR (n:Phone) REQUIRE n.number IS UNIQUE;
CREATE CONSTRAINT username_unique IF NOT EXISTS FOR (n:Username) REQUIRE (n.value, n.platform) IS UNIQUE;
CREATE CONSTRAINT domain_unique IF NOT EXISTS FOR (n:Domain) REQUIRE n.name IS UNIQUE;

// Create indexes for performance
CREATE INDEX identity_id IF NOT EXISTS FOR (n:Identity) ON (n.id);
CREATE INDEX identity_name IF NOT EXISTS FOR (n:Identity) ON (n.name);
CREATE INDEX email_address IF NOT EXISTS FOR (n:Email) ON (n.address);
CREATE INDEX phone_number IF NOT EXISTS FOR (n:Phone) ON (n.number);
CREATE INDEX username_value IF NOT EXISTS FOR (n:Username) ON (n.value);
CREATE INDEX username_platform IF NOT EXISTS FOR (n:Username) ON (n.platform);
CREATE INDEX domain_name IF NOT EXISTS FOR (n:Domain) ON (n.name);
CREATE INDEX social_profile IF NOT EXISTS FOR (n:SocialMedia) ON (n.profile_url);
CREATE INDEX social_platform IF NOT EXISTS FOR (n:SocialMedia) ON (n.platform);
CREATE INDEX adult_profile IF NOT EXISTS FOR (n:AdultProfile) ON (n.profile_url);
CREATE INDEX adult_platform IF NOT EXISTS FOR (n:AdultProfile) ON (n.platform);
CREATE INDEX personals_post IF NOT EXISTS FOR (n:PersonalsPost) ON (n.post_id);
CREATE INDEX personals_site IF NOT EXISTS FOR (n:PersonalsPost) ON (n.site);
CREATE INDEX address_location IF NOT EXISTS FOR (n:Address) ON (n.location);

// Node types and their properties (documentation):
// 
// Identity: {id, name, type, created_at}
// Email: {address, domain, verified, created_at}
// Phone: {number, country_code, carrier, created_at}
// Username: {value, platform, created_at}
// Domain: {name, registrar, registration_date, created_at}
// SocialMedia: {platform, profile_url, username, display_name, bio, followers, created_at}
// Address: {location, city, state, country, postal_code, created_at}
// AdultProfile: {platform, profile_url, username, description, media_urls, created_at}
// PersonalsPost: {post_id, site, title, description, phone, email, location, posted_date, created_at}
//
// Relationship types:
// LINKED_TO: General connection between entities
// MENTIONED_IN: Entity mentioned in content
// REGISTERED_ON: User registered on a platform
// CONNECTED_VIA: Connection through intermediate entity
// POSTED_ON: Content posted on platform
// ASSOCIATED_WITH: General association
// LOCATED_AT: Geographic location
// OWNS: Ownership relationship
// USES: Usage relationship (e.g., uses email, uses phone)
//
// Relationship properties: {confidence, source, timestamp, evidence}
