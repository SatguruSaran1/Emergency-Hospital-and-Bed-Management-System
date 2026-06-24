-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: emergency_hospital_db
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `emergency_hospital_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `emergency_hospital_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `emergency_hospital_db`;

--
-- Table structure for table `admission`
--

DROP TABLE IF EXISTS `admission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admission` (
  `admission_id` int NOT NULL,
  `admission_date` datetime NOT NULL,
  `discharge_date` date DEFAULT NULL,
  `status` enum('Active','Discharged','Transferred') DEFAULT 'Active',
  `patient_id` int NOT NULL,
  `doctor_id` int NOT NULL,
  `bed_id` int NOT NULL,
  PRIMARY KEY (`admission_id`),
  KEY `patient_id` (`patient_id`),
  KEY `doctor_id` (`doctor_id`),
  KEY `admission_ibfk_3` (`bed_id`),
  CONSTRAINT `admission_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`patient_id`),
  CONSTRAINT `admission_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`doctor_id`),
  CONSTRAINT `admission_ibfk_3` FOREIGN KEY (`bed_id`) REFERENCES `bed` (`bed_id`),
  CONSTRAINT `chk_dates` CHECK (((`discharge_date` is null) or (`discharge_date` >= `admission_date`)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admission`
--

LOCK TABLES `admission` WRITE;
/*!40000 ALTER TABLE `admission` DISABLE KEYS */;
INSERT INTO `admission` VALUES (601,'2026-02-01 00:00:00',NULL,'Active',301,201,1001),(602,'2026-02-02 00:00:00','2026-04-09','Discharged',302,202,1002),(603,'2026-02-02 00:00:00','2026-03-15','Discharged',303,203,1003),(604,'2026-02-03 00:00:00',NULL,'Active',304,204,1004),(605,'2026-02-03 00:00:00',NULL,'Active',305,205,1005),(606,'2026-02-04 00:00:00',NULL,'Active',306,206,1006),(607,'2026-02-04 00:00:00',NULL,'Active',307,207,1007),(608,'2026-02-05 00:00:00','2026-03-15','Discharged',308,208,1008),(609,'2026-02-05 00:00:00',NULL,'Active',309,209,1009),(610,'2026-02-06 00:00:00',NULL,'Active',310,210,1010),(611,'2026-03-15 00:00:00',NULL,'Active',308,201,1003);
/*!40000 ALTER TABLE `admission` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_after_admission_insert` AFTER INSERT ON `admission` FOR EACH ROW BEGIN
    UPDATE bed SET status = 'Occupied' WHERE bed_id = NEW.bed_id;
    UPDATE doctor SET availability_status = 'Busy' WHERE doctor_id = NEW.doctor_id;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `bed`
--

DROP TABLE IF EXISTS `bed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bed` (
  `bed_id` int NOT NULL,
  `bed_type` varchar(50) NOT NULL,
  `status` enum('Available','Occupied','Maintenance') DEFAULT 'Available',
  `ward_id` int NOT NULL,
  PRIMARY KEY (`bed_id`),
  KEY `ward_id` (`ward_id`),
  CONSTRAINT `bed_ibfk_1` FOREIGN KEY (`ward_id`) REFERENCES `ward` (`ward_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bed`
--

LOCK TABLES `bed` WRITE;
/*!40000 ALTER TABLE `bed` DISABLE KEYS */;
INSERT INTO `bed` VALUES (1001,'ICU','Occupied',101),(1002,'ICU','Available',101),(1003,'General','Occupied',102),(1004,'General','Occupied',103),(1005,'Emergency','Occupied',104),(1006,'ICU','Occupied',105),(1007,'General','Occupied',106),(1008,'Emergency','Available',107),(1009,'ICU','Occupied',108),(1010,'General','Occupied',109);
/*!40000 ALTER TABLE `bed` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctor`
--

DROP TABLE IF EXISTS `doctor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doctor` (
  `doctor_id` int NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `specialization` varchar(100) DEFAULT NULL,
  `availability_status` enum('Available','Busy','On Leave','Fatigued') DEFAULT 'Available',
  `fatigued_until` datetime DEFAULT NULL,
  PRIMARY KEY (`doctor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctor`
--

LOCK TABLES `doctor` WRITE;
/*!40000 ALTER TABLE `doctor` DISABLE KEYS */;
INSERT INTO `doctor` VALUES (201,'Dr. Sharma','Cardiology','Busy',NULL),(202,'Dr. Mehta','Neurology','Busy',NULL),(203,'Dr. Singh','Orthopedics','Available',NULL),(204,'Dr. Rao','General','Available',NULL),(205,'Dr. Khan','Pediatrics','Busy',NULL),(206,'Dr. Patel','Dermatology','Available',NULL),(207,'Dr. Das','Emergency','Available',NULL),(208,'Dr. Verma','ENT','Available',NULL),(209,'Dr. Roy','Surgery','Available',NULL),(210,'Dr. Joshi','ICU','Available',NULL);
/*!40000 ALTER TABLE `doctor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctor_user_map`
--

DROP TABLE IF EXISTS `doctor_user_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doctor_user_map` (
  `username` varchar(50) NOT NULL,
  `doctor_id` int NOT NULL,
  PRIMARY KEY (`username`),
  KEY `doctor_id` (`doctor_id`),
  CONSTRAINT `doctor_user_map_ibfk_1` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`doctor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctor_user_map`
--

LOCK TABLES `doctor_user_map` WRITE;
/*!40000 ALTER TABLE `doctor_user_map` DISABLE KEYS */;
INSERT INTO `doctor_user_map` VALUES ('doctor1',201),('doctor2',202),('doctor3',203),('doctor4',204),('doctor5',205),('doctor6',206),('doctor7',207),('doctor8',208),('doctor9',209),('doctor10',210);
/*!40000 ALTER TABLE `doctor_user_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hospital`
--

DROP TABLE IF EXISTS `hospital`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hospital` (
  `hospital_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `location` varchar(100) DEFAULT NULL,
  `contact_no` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`hospital_id`),
  CONSTRAINT `chk_hospital_name` CHECK ((trim(`name`) <> _cp850''))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hospital`
--

LOCK TABLES `hospital` WRITE;
/*!40000 ALTER TABLE `hospital` DISABLE KEYS */;
INSERT INTO `hospital` VALUES (1,'Apollo Hospitals Delhi','New Delhi','9911100001');
/*!40000 ALTER TABLE `hospital` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory`
--

DROP TABLE IF EXISTS `inventory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory` (
  `inventory_id` int NOT NULL,
  `quantity` int NOT NULL,
  `threshold_level` int NOT NULL,
  `hospital_id` int NOT NULL,
  `resource_id` int NOT NULL,
  PRIMARY KEY (`inventory_id`),
  KEY `hospital_id` (`hospital_id`),
  KEY `resource_id` (`resource_id`),
  CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`),
  CONSTRAINT `inventory_ibfk_2` FOREIGN KEY (`resource_id`) REFERENCES `resource` (`resource_id`),
  CONSTRAINT `chk_quantity_positive` CHECK ((`quantity` >= 0)),
  CONSTRAINT `chk_threshold_positive` CHECK ((`threshold_level` >= 0)),
  CONSTRAINT `inventory_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory`
--

LOCK TABLES `inventory` WRITE;
/*!40000 ALTER TABLE `inventory` DISABLE KEYS */;
INSERT INTO `inventory` VALUES (501,50,10,1,401),(502,6,2,1,402),(503,200,50,1,403),(504,300,80,1,404),(505,150,40,1,405),(506,20,5,1,406),(507,10,2,1,407),(508,15,3,1,408),(509,7,2,1,409),(510,500,100,1,410),(511,120,30,1,401);
/*!40000 ALTER TABLE `inventory` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_inventory_check` AFTER UPDATE ON `inventory` FOR EACH ROW BEGIN
            IF NEW.quantity <= NEW.threshold_level AND OLD.quantity > NEW.threshold_level THEN
                INSERT INTO notification (message, type)
                VALUES (
                    CONCAT('Low Stock Alert: "', 
                           (SELECT resource_name FROM resource WHERE resource_id = NEW.resource_id), 
                           '" is at ', NEW.quantity, ' (Threshold: ', NEW.threshold_level, ')'),
                    'Critical'
                );
            END IF;
        END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `notification`
--

DROP TABLE IF EXISTS `notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notification` (
  `notification_id` int NOT NULL AUTO_INCREMENT,
  `message` varchar(255) NOT NULL,
  `type` enum('Info','Warning','Critical') DEFAULT 'Warning',
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`notification_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notification`
--

LOCK TABLES `notification` WRITE;
/*!40000 ALTER TABLE `notification` DISABLE KEYS */;
INSERT INTO `notification` VALUES (1,'Low Stock Alert: \"Oxygen Cylinder\" is at 11 (Threshold: 30)','Critical',1,'2026-03-19 02:35:53'),(2,'Low Stock Alert: \"Oxygen Cylinder\" is at 9 (Threshold: 10)','Critical',1,'2026-03-19 02:35:53'),(3,'Low Stock Alert: \"Defibrillator\" is at 1 (Threshold: 2)','Critical',1,'2026-03-19 02:42:11'),(4,'Low Stock Alert: \"Saline Bottle\" is at 39 (Threshold: 40)','Critical',1,'2026-03-19 02:42:42'),(5,'Low Stock Alert: \"Wheelchair\" is at 1 (Threshold: 2)','Critical',1,'2026-03-19 11:38:53'),(6,'Low Stock Alert: \"Ventilator\" is at 1 (Threshold: 2)','Critical',1,'2026-04-02 00:55:17'),(7,'Low Stock Alert: \"Oxygen Cylinder\" is at 0 (Threshold: 10)','Critical',1,'2026-04-02 02:01:03'),(8,'Low Stock Alert: \"Ventilator\" is at 1 (Threshold: 2)','Critical',1,'2026-04-02 15:05:36'),(9,'Low Stock Alert: \"Ventilator\" is at 1 (Threshold: 2)','Critical',1,'2026-04-18 15:51:35');
/*!40000 ALTER TABLE `notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patient`
--

DROP TABLE IF EXISTS `patient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient` (
  `patient_id` int NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `age` int DEFAULT NULL,
  `gender` enum('Male','Female','Other') DEFAULT NULL,
  `emergency_level` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`patient_id`),
  CONSTRAINT `chk_age_valid` CHECK ((`age` between 0 and 120))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patient`
--

LOCK TABLES `patient` WRITE;
/*!40000 ALTER TABLE `patient` DISABLE KEYS */;
INSERT INTO `patient` VALUES (301,'Amit',25,'Male','High'),(302,'Priya',30,'Female','Medium'),(303,'Rahul',40,'Male','Low'),(304,'Sneha',19,'Female','High'),(305,'Arjun',60,'Male','Critical'),(306,'Neha',45,'Female','Medium'),(307,'Rohan',50,'Male','Low'),(308,'Kriti',27,'Female','High'),(309,'Manoj',33,'Male','Medium'),(310,'Ananya',22,'Female','Low'),(1001,'Riya',35,'Female','High');
/*!40000 ALTER TABLE `patient` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resource`
--

DROP TABLE IF EXISTS `resource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `resource` (
  `resource_id` int NOT NULL,
  `resource_name` varchar(100) NOT NULL,
  PRIMARY KEY (`resource_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `resource`
--

LOCK TABLES `resource` WRITE;
/*!40000 ALTER TABLE `resource` DISABLE KEYS */;
INSERT INTO `resource` VALUES (401,'Oxygen Cylinder'),(402,'Ventilator'),(403,'Syringe Kit'),(404,'Gloves Box'),(405,'Saline Bottle'),(406,'Monitor'),(407,'Wheelchair'),(408,'Stretcher'),(409,'Defibrillator'),(410,'Mask Pack');
/*!40000 ALTER TABLE `resource` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(200) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `role` enum('admin','doctor') DEFAULT 'admin',
  `doctor_id` int DEFAULT NULL,
  PRIMARY KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('admin','9424089ec624fd72031defa65daeb005:3f9f7cf26ee39fb7c047569df6559b3cce65a5a726a48ad5835f150ab2882238','2026-03-18 13:23:37','admin',NULL),('admin1','1dd69a82b8c5e97fe0ab03281b34d17e:23beee4466f95d7dbd3e9a28a3d426f25ef41e001d4055e302baf7da461483a7','2026-03-18 18:14:52','admin',NULL),('admin10','d87143f669cc3d37e90698680d88c3a2:570c996feb27b20fd15c25b6618a3ae374d943cd5fdea53ab6a5dbca15cfbc35','2026-03-18 18:14:52','admin',NULL),('admin2','088bffb5a500777190d9e010784e4b5e:d6fd02eea82c74579ccc4fc160f544ee7d9ac076a40a24693560f0f82bf0b348','2026-03-18 18:14:52','admin',NULL),('admin3','ed1416becbdc4485c6e2422958729c83:58d66cb77653684f66d6b68521b57819dc64ebe9100cfc0709ac6bb2297feada','2026-03-18 18:14:52','admin',NULL),('admin4','494d55499dc6f976a942ec7f8fe88b8f:ead246a5e18c997eff3a8756b32da3020b3f5afc0f0ae008392289f993a7e108','2026-03-18 18:14:52','admin',NULL),('admin5','e38c8ba9bb8c85c89d33573f0a001390:052c98d353df3504ffdaee9aa0224738988c34f4061db463028509fd303b8cc5','2026-03-18 18:14:52','admin',NULL),('admin6','c83fa6cedc3b13945e39d1429dfbc2ee:1f79135ab93a06656cdc521bc1bffdb845aafbd10239a56b2a7c314c7450e7cc','2026-03-18 18:14:52','admin',NULL),('admin7','057411c579ab099bbef834648509e4f6:a1212a6f2c6667f15fde66b86be176939ff01947f2a186dc33569af9d142ec51','2026-03-18 18:14:52','admin',NULL),('admin8','a7fb068f8663c744582065e97e5519c6:bd8f14d0cd5f4e9237e911507294fe4c4019dd3da2c44a0ea21a0fdf49ae3a4b','2026-03-18 18:14:52','admin',NULL),('admin9','3f3da75df94ff1660c1bddb7d111700f:3b0d8b59f8f5e7408e257ce2e41372a507cb418634fd72380ed9160c353c8f65','2026-03-18 18:14:52','admin',NULL),('doctor1','fb5cc3338c54d26e1188a9032e5ae9fc:a4cd0144fc451867dbd4c753ceb2d19d2fb5e1776723ee80085f2824eab2d42a','2026-04-09 09:21:13','doctor',NULL),('doctor10','2faee1e28f2a9fb209eb53723486370b:63b56635d3891627a93ed8852eb482387cb63149db32f705c5a7a27358dad93f','2026-04-09 09:21:14','doctor',NULL),('doctor2','28c7455f9df2b8f31a4b2f216c327ab7:e2f72882d35c06dcdd334a9a4cb9dc63ee5293fcee81a7d9bcbd0eaaca1eaeb2','2026-04-09 09:21:13','doctor',NULL),('doctor3','676ce78fdac9279ccf9325836445805d:37a18e6791b1ec23b51ca1bec6e6a2bb8c51e2fe6154d1316a5de93571b91289','2026-04-09 09:21:13','doctor',NULL),('doctor4','ad7ef5fdbedc08010d2b9eac69787382:66a8caf3e159bcd6826fcce0a98f46e782dfb217e4a35b7e36db33b064adba36','2026-04-09 09:21:14','doctor',NULL),('doctor5','408fc45eae55d930b75b5f698caac312:87e3685be959d61952ec309b71e06186fa655db9676043d16fc01d506cb633a5','2026-04-09 09:21:14','doctor',NULL),('doctor6','eba66d77fce913442454a70decd65fdd:ff049afadf66547c5d7cbad87f8accc1b31aa9c748dec0ee1e7150afde2c56a2','2026-04-09 09:21:14','doctor',NULL),('doctor7','bd0da2dd70dfa30017bc2a79a168febc:db2d800ae01679c807070b15b2973aefad538fdaec68a153a82b065f1cd7fbb6','2026-04-09 09:21:14','doctor',NULL),('doctor8','3c55c75721aa6fc96d568792f80ffbd2:6a120088f9534aa4f7ea81851ff36ab21c5a25dc08ebbd51a6fdc435b5b5afcf','2026-04-09 09:21:14','doctor',NULL),('doctor9','3891fdd42efebf0a743f5d8b9920c196:b1438a6726749dfe9c6c8fe49233bc95ad24a4ac1c461a4812c0263d1ffae554','2026-04-09 09:21:14','doctor',NULL),('drdas207','1d3872192224394bc259767a25fa3326:965a31127098cdc81c98e96b1218fb4de5f45e1483269ed9b5f5aed7bbd38181','2026-04-18 09:32:16','doctor',207),('drjoshi210','96544255a0956dae1abe3b06ad10b2ca:5a1c1a9a5b17ac057463201d99fef6aedf5fd912a2495087b8ef7001914c9de9','2026-04-18 09:32:16','doctor',210),('drkhan205','0b7208f96d1b36cc049db2a821f8d8f2:6ce3e1fed84ffce06673c0389c6dba945db1b3f994125eadb7341cffe1004d2e','2026-04-18 09:32:16','doctor',205),('drmehta202','730100209389f1419545565715a4f0a9:6045a5fb7ff09a16dfb479a2806da41ee352cd8f471279cfee70849fa0303e59','2026-04-18 09:32:16','doctor',202),('drpatel206','3f2aff8d1c6efb3d263bb8afca232126:8db67a7272232e809a079ebd54d5b8d73cf5c2b257b7ec3f0aef5cfc80a945d7','2026-04-18 09:32:16','doctor',206),('drrao204','3ac6131c5ba81ae998825a0573bd6d12:4d1799e1c0d043c061c10ee6bd1d80b9122f60e8f9de7f11311f5dd898ceaad9','2026-04-18 09:32:16','doctor',204),('drroy209','dff335f413e7b08b19e69430238f9859:df049540eb24cee860ed7feb4600d3f223c100d461fbc6a7ac3d08d9acb44bb8','2026-04-18 09:32:16','doctor',209),('drsharma201','b1bfba57a6a99afaf7305806f6e5d68c:be865167e08f5494e77b8b52113036aa936322f08f5d172c9c97609eb1e7814b','2026-04-18 09:32:16','doctor',201),('drsingh203','97901850fd45df70782b0819919651bd:6b4b78da16fcf15da86c3ccb6bb5c568e85d428e1a3bd151dc34f4e6179a7653','2026-04-18 09:32:16','doctor',203),('drverma208','b68e75e5db7aa08ba6c11a707b0fd9a2:974f93ca1ffb311adc24302dcbfbe5033eb9ab6abe5b6145d4c163ada7117ad3','2026-04-18 09:32:16','doctor',208);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ward`
--

DROP TABLE IF EXISTS `ward`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ward` (
  `ward_id` int NOT NULL,
  `ward_type` varchar(50) DEFAULT NULL,
  `capacity` int NOT NULL,
  `hospital_id` int NOT NULL,
  PRIMARY KEY (`ward_id`),
  KEY `hospital_id` (`hospital_id`),
  CONSTRAINT `ward_ibfk_1` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`),
  CONSTRAINT `chk_capacity_positive` CHECK ((`capacity` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ward`
--

LOCK TABLES `ward` WRITE;
/*!40000 ALTER TABLE `ward` DISABLE KEYS */;
INSERT INTO `ward` VALUES (101,'ICU',10,1),(102,'General',20,1),(103,'ICU',8,1),(104,'General',25,1),(105,'Emergency',12,1),(106,'ICU',10,1),(107,'General',18,1),(108,'Emergency',15,1),(109,'General',22,1),(110,'ICU',9,1);
/*!40000 ALTER TABLE `ward` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'emergency_hospital_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-18 16:10:36
