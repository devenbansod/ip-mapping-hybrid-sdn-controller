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
