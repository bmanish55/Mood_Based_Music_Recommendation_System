-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Jun 24, 2025 at 04:01 PM
-- Server version: 8.0.36
-- PHP Version: 8.2.13

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `moodbeats`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
CREATE TABLE IF NOT EXISTS `admins` (
  `admin_id` int NOT NULL AUTO_INCREMENT,
  `admin_name` varchar(50) NOT NULL,
  `admin_username` varchar(50) NOT NULL,
  `admin_password` varchar(255) NOT NULL,
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `admin_username` (`admin_username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`admin_id`, `admin_name`, `admin_username`, `admin_password`) VALUES
(1, 'Vishal Taskar', 'admin', 'scrypt:32768:8:1$e7tmxidHacwyYGtf$744bed89a376cde7df336608495f0cce12e772edd18965dbdeed65d2a4f8d43b7a45f1f358c3edf86822568e9a0494fdeef809faccbf03eb4315fe5bd652bb70');

-- --------------------------------------------------------

--
-- Table structure for table `favorites`
--

DROP TABLE IF EXISTS `favorites`;
CREATE TABLE IF NOT EXISTS `favorites` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `song_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `song_id` (`song_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `favorites`
--

INSERT INTO `favorites` (`id`, `user_id`, `song_id`, `created_at`) VALUES
(3, 1, 3, '2025-06-13 10:10:20'),
(4, 1, 1, '2025-06-13 10:10:24'),
(5, 1, 4, '2025-06-13 11:51:10'),
(6, 1, 5, '2025-06-13 11:51:15');

-- --------------------------------------------------------

--
-- Table structure for table `history`
--

DROP TABLE IF EXISTS `history`;
CREATE TABLE IF NOT EXISTS `history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `mood` varchar(50) NOT NULL,
  `playedsong` varchar(255) NOT NULL,
  `song_artist` varchar(255) DEFAULT NULL,
  `song_url` varchar(255) DEFAULT NULL,
  `day_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `history`
--

INSERT INTO `history` (`id`, `user_id`, `mood`, `playedsong`, `song_artist`, `song_url`, `day_date`) VALUES
(2, 1, 'fear', 'Flying: Relaxing Sleep Music for Meditation, Stress Relief & Relaxation by Peder B. Helland', 'Soothing Relaxation', 'https://music.youtube.com/watch?v=1ZYbU82GVz4', '2025-06-12 18:54:14'),
(3, 1, 'fear', 'OFFICIAL: Best Soothing Songs of Bollywood | Soothing Music', 'T-Series', 'https://music.youtube.com/watch?v=SQ1ED8-tBpE', '2025-06-12 18:54:23'),
(4, 1, 'sad', 'Tabaah Ho Gaye Heartbreak Hits 💔 | Non-Stop Sad Songs | Rula Ke Gaya Ishq & More', 'Zee Music Company', 'https://music.youtube.com/watch?v=F2XIe4lymaU', '2025-06-13 13:04:43'),
(5, 1, 'angry', 'Slipknot - Psychosocial [OFFICIAL VIDEO] [HD]', 'Slipknot', 'https://music.youtube.com/watch?v=5abamRO41fE', '2025-06-13 17:35:08');

-- --------------------------------------------------------

--
-- Table structure for table `playlists`
--

DROP TABLE IF EXISTS `playlists`;
CREATE TABLE IF NOT EXISTS `playlists` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `song_count` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `playlists`
--

INSERT INTO `playlists` (`id`, `user_id`, `name`, `song_count`, `created_at`) VALUES
(2, 1, 'mitraz', 2, '2025-06-12 12:50:54');

-- --------------------------------------------------------

--
-- Table structure for table `playlist_songs`
--

DROP TABLE IF EXISTS `playlist_songs`;
CREATE TABLE IF NOT EXISTS `playlist_songs` (
  `playlist_id` int NOT NULL,
  `song_id` int NOT NULL,
  PRIMARY KEY (`playlist_id`,`song_id`),
  KEY `song_id` (`song_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `playlist_songs`
--

INSERT INTO `playlist_songs` (`playlist_id`, `song_id`) VALUES
(2, 1),
(2, 2);

-- --------------------------------------------------------

--
-- Table structure for table `songs`
--

DROP TABLE IF EXISTS `songs`;
CREATE TABLE IF NOT EXISTS `songs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `artist` varchar(255) DEFAULT NULL,
  `url` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `songs`
--

INSERT INTO `songs` (`id`, `title`, `artist`, `url`) VALUES
(1, 'Feel Good Hindi Songs | Audio Jukebox | Upbeat Bollywood Songs', 'YRF Music', 'https://music.youtube.com/watch?v=pIvf9bOPXIw'),
(2, 'Slipknot - Psychosocial [OFFICIAL VIDEO] [HD]', 'Slipknot', 'https://music.youtube.com/watch?v=5abamRO41fE'),
(3, 'Sad break up song arijit singh heart touching sad song {Arijit Singh}', 'Alone Bhai K Ringtones ', 'https://music.youtube.com/watch?v=1BKbzZhvUAI'),
(4, '||TOP HITS OF MITRAZ 🔥|| @MITRAZ @HYMusicStudio #viral #mitraz #song #album #mitraznewsong', 'HY Music Studio ', 'https://music.youtube.com/watch?v=Ykapjl0xe2Y'),
(5, 'MITRAZ Mashup | chill mood songs | AR music', 'AR Music', 'https://music.youtube.com/watch?v=Zu4kVFOBP20');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `email_notifications` tinyint(1) DEFAULT '1',
  `explicit_content` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `created_at`, `email_notifications`, `explicit_content`) VALUES
(1, 'vishaltaskar', 'vishaltaskar16@gmail.com', 'scrypt:32768:8:1$kTlNGctBNLZ55l9l$d4fa40e9c6dcda85a19ce51db9fc550ea629f52f968e3d362ecd63b4f3731bb6a419e15e9bc1fd706c7205dff5f6bb87eec86cb58ae815fef67ee762d281d40f', '2025-06-12 12:28:30', 1, 0);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `favorites`
--
ALTER TABLE `favorites`
  ADD CONSTRAINT `favorites_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `favorites_ibfk_2` FOREIGN KEY (`song_id`) REFERENCES `songs` (`id`);

--
-- Constraints for table `history`
--
ALTER TABLE `history`
  ADD CONSTRAINT `history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `playlists`
--
ALTER TABLE `playlists`
  ADD CONSTRAINT `playlists_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `playlist_songs`
--
ALTER TABLE `playlist_songs`
  ADD CONSTRAINT `playlist_songs_ibfk_1` FOREIGN KEY (`playlist_id`) REFERENCES `playlists` (`id`),
  ADD CONSTRAINT `playlist_songs_ibfk_2` FOREIGN KEY (`song_id`) REFERENCES `songs` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
