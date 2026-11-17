-- 调岗更正：部门生效区间登记（双时态）、更正单状态机、辅导转交依据。
-- 区间登记只增不改，保留更正前认知；归属按知悉时点还原。
CREATE TABLE `corrections` (
  `id` int NOT NULL AUTO_INCREMENT,
  `learner` varchar(60) NOT NULL,
  `department` varchar(60) NOT NULL,
  `valid_from` varchar(10) NOT NULL,
  `valid_to` varchar(10) DEFAULT NULL,
  `registered_at` varchar(40) NOT NULL,
  `status` varchar(20) DEFAULT 'processing',
  PRIMARY KEY (`id`),
  KEY `ix_corrections_learner` (`learner`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `department_assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `learner` varchar(60) NOT NULL,
  `department` varchar(60) NOT NULL,
  `valid_from` varchar(10) NOT NULL,
  `valid_to` varchar(10) DEFAULT NULL,
  `registered_at` varchar(40) NOT NULL,
  `correction_id` int DEFAULT NULL,
  `note` text,
  PRIMARY KEY (`id`),
  KEY `ix_department_assignments_learner` (`learner`),
  CONSTRAINT `department_assignments_ibfk_1` FOREIGN KEY (`correction_id`) REFERENCES `corrections` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `transfers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `correction_id` int NOT NULL,
  `intervention_id` int NOT NULL,
  `learner` varchar(60) NOT NULL,
  `from_department` varchar(60) DEFAULT NULL,
  `to_department` varchar(60) DEFAULT NULL,
  `created` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_transfer` (`correction_id`,`intervention_id`,`learner`),
  KEY `intervention_id` (`intervention_id`),
  CONSTRAINT `transfers_ibfk_1` FOREIGN KEY (`correction_id`) REFERENCES `corrections` (`id`),
  CONSTRAINT `transfers_ibfk_2` FOREIGN KEY (`intervention_id`) REFERENCES `interventions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE `cohorts` ADD COLUMN `known_at` varchar(40) DEFAULT NULL;
ALTER TABLE `interventions` ADD COLUMN `attributions` json DEFAULT NULL;
