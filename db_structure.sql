CREATE TABLE `devices` (
	`device_id` INT(10) NOT NULL PRIMARY KEY,
	`name` VARCHAR(50) NOT NULL,
	`details` TEXT
);

CREATE TABLE `interfaces` (
	`global_int_id` INT (10) NOT NULL,
	`int_id` VARCHAR(50) NOT NULL,
	`device_id` INT(10) NOT NULL,
	`mac_addr` varchar(25),
	`ip_addr` varchar(15),
	`name` VARCHAR(25),

	PRIMARY KEY (`global_int_id`),
	CONSTRAINT `devices_int_fk` FOREIGN KEY (`device_id`)
	REFERENCES `devices` (`device_id`) ON DELETE RESTRICT
);


CREATE TABLE `links` (
	`link_id` INT (10) NOT NULL,
	`int1` INT (10) NOT NULL,
	`int2` INT (10) NOT NULL,

	PRIMARY KEY (`link_id`),
	CONSTRAINT `int_links_fk` FOREIGN KEY (`int1`)
	REFERENCES `interfaces` (`global_int_id`) ON DELETE CASCADE,
	CONSTRAINT `int_links_fk_2` FOREIGN KEY (`int2`)
	REFERENCES `interfaces` (`global_int_id`) ON DELETE CASCADE
);

-- INSERT INTO devices VALUES 
-- 	(1, 's1', ''),
-- 	(2, 's2', ''),
-- 	(3, 'r3', '{"username": "zebra", "password": "zebra", "ip" : "127.0.0.1", "port" : "2601"}'),
-- 	(4, 'r4', '{"username": "zebra", "password": "zebra", "ip" : "127.0.0.1", "port" : "2601"}'),
-- 	(5, 'h1', ''),
-- 	(6, 'h2', '');


-- INSERT INTO interfaces VALUES
-- 	(1, 1, 1, '00:00:00:00:01:01', '', 's1-eth1'),
-- 	(2, 2, 1, '00:00:00:00:01:02', '', 's1-eth2'),
-- 	(3, 3, 1, '00:00:00:00:01:03', '', 's1-eth3'),
-- 	(4, 1, 2, '00:00:00:00:02:01', '', 's2-eth1'),
-- 	(5, 2, 2, '00:00:00:00:02:02', '', 's2-eth2'),
-- 	(6, 3, 2, '00:00:00:00:02:03', '', 's2-eth3'),
-- 	(7, 'r3-eth0', 3, '00:00:00:00:03:01', '10.0.1.3', 'r3-eth0'),
-- 	(8, 'r3-eth1', 3, '00:00:00:00:03:02', '10.0.2.3', 'r3-eth1'),
-- 	(9, 'r4-eth0', 4, '00:00:00:00:04:01', '10.0.1.4', 'r4-eth0'),
-- 	(10, 'r4-eth1', 4, '00:00:00:00:04:02', '10.0.2.4', 'r4-eth1'), 
-- 	(11, 'h1-eth0', 5, '00:00:00:00:00:01', '10.0.1.10', 'h1-eth0'),
-- 	(12, 'h2-eth0', 6, '00:00:00:00:00:02', '10.0.2.10', 'h2-eth0');

-- INSERT INTO links VALUES 
-- 	(1, 11, 1),
-- 	(2, 12, 4),
-- 	(3, 9, 3),
-- 	(4, 10, 6),
-- 	(5, 8, 5),
-- 	(6, 7, 2);