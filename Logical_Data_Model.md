Entity (#id : INT , displayName: STRING, createdAt: DATE, entity_near => Entity(id)) 

Entity_Proximity ( #Entity1_Proximity => Entity (id), # Entity2_Proximity (Entity(id)), distance_m : INT )

Service(id INT PRIMARY KEY, title STRING NOT NULL, type STRING NOT NULL CHECK (type IN ('FREE', 'EXCHANGE', 'COMMERCIAL_G1')),description STRING, entity_id INT NOT NULL => Entity(id)
)
 

EntitySkill ( #id : INT, level : INT, entity_id : INT  NOT NULL => Entity, skill_id : INT  NOT NULL => Skill CHECK (level BETWEEN 1 AND 5)) 

Skill ( #id : INT, label : STRING, description : STRING)

Individual ( #id_individual => Entity(id), email : STRING UNIQUE, latitude: INT, longitude : INT) 

Community (  #id_community => Entity(id), name : STRING UNIQUE, description: STRING)  

vIndividual = join(Entity, Individual, Entity.id = Individual.id )

vCommunity = join(Entity, Community, Entity.id = Community.id )

vProximity = JOIN(Individual i1, Individual i2, Entity e1, Entity e2,
                  i1.id_individual = e1.id AND i2.id_individual = e2.id)
             WHERE i1.id_individual ≠ i2.id_individual

Community_Collaboration ( #id_community1 => Community(id_community), #id_community2 => Community(id_community) )

Individual_Connexion ( #id_individual1 => Individual(id_individual), #id_individual2 => Individual(id_individual))

Membership (# id : INT, joinedAt : DATE, isExcluded: BOOLEAN, id_community: INT NOT NULL => Community (id_community), id_individual: INT NOT NULL=> individual(id_individual)) 

ExclusionVote ( #id : INT, votedAt : DATE, vote : BOOLEAN, membership_id : INT  NOT NULL => Membership(id)) 

G1Account(#id : INT, #publicKey NOT NULL UNIQUE : STRING, entity_id: INT  NOT NULL => Entity(id))

Message(#id : INT, SentAt : DATE, Subject: STRING, body: STRING, sender_id : INT  NOT NULL => Entity(id) , recipient_id : INT  NOT NULL => Entity(id) , InReplyTo_id : INT NOT NULL  => Message(id)  )

