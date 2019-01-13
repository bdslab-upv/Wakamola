CREATE TABLE IF NOT EXISTS STATUS (id_user varchar(32) PRIMARY KEY, phase int NOT NULL, question int NOT NULL,
completed_personal int, completed_food int, completed_activity int, language text, last_wakaestado float);

CREATE TABLE IF NOT EXISTS QUESTIONS (question int, phase int, qtext text, language varchar(2),
PRIMARY KEY (question, phase, language), UNIQUE(question, phase, language));

CREATE TABLE IF NOT EXISTS RESPONSES (id_user varchar(32), id_message int, question int, phase int, answer float,
Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (id_user, id_message, question, phase));

CREATE TABLE IF NOT EXISTS RELATIONSHIPS (active varchar(32), passive varchar(32), type varchar(20),
Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(active, passive),
FOREIGN KEY (active) references STATUS (id_user));



