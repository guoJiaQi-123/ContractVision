-- ContractVision 数据库初始化脚本
-- 适用于 MySQL 8.0+
-- 账号: root / 密码: 请替换为本地 MySQL 密码 / 端口: 3306

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `contract_vision` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `contract_vision`;

-- ========================================
-- Django 框架内置表
-- ========================================

-- Django Content Type
CREATE TABLE IF NOT EXISTS `django_content_type` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `app_label` VARCHAR(100) NOT NULL,
    `model` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `django_content_type_app_label_model_uniq` (`app_label`, `model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Django Migrations
CREATE TABLE IF NOT EXISTS `django_migrations` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `app` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `applied` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Django Admin Log
CREATE TABLE IF NOT EXISTS `django_admin_log` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `action_time` DATETIME(6) NOT NULL,
    `object_id` LONGTEXT,
    `object_repr` VARCHAR(200) NOT NULL,
    `action_flag` SMALLINT UNSIGNED NOT NULL,
    `change_message` LONGTEXT NOT NULL,
    `content_type_id` INT DEFAULT NULL,
    `user_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    KEY `django_admin_log_content_type_id_fk` (`content_type_id`),
    KEY `django_admin_log_user_id_fk` (`user_id`),
    CONSTRAINT `django_admin_log_content_type_id_fk` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Django Session
CREATE TABLE IF NOT EXISTS `django_session` (
    `session_key` VARCHAR(40) NOT NULL,
    `session_data` LONGTEXT NOT NULL,
    `expire_date` DATETIME(6) NOT NULL,
    PRIMARY KEY (`session_key`),
    KEY `django_session_expire_date_idx` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- Django Auth 权限表
-- ========================================

-- Auth Permission
CREATE TABLE IF NOT EXISTS `auth_permission` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `content_type_id` INT NOT NULL,
    `codename` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_permission_content_type_id_codename_uniq` (`content_type_id`, `codename`),
    CONSTRAINT `auth_permission_content_type_id_fk` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Auth Group
CREATE TABLE IF NOT EXISTS `auth_group` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(150) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_group_name_uniq` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Auth Group Permissions
CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `group_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_group_permissions_group_id_permission_id_uniq` (`group_id`, `permission_id`),
    KEY `auth_group_permissions_group_id_fk` (`group_id`),
    KEY `auth_group_permissions_permission_id_fk` (`permission_id`),
    CONSTRAINT `auth_group_permissions_group_id_fk` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
    CONSTRAINT `auth_group_permissions_permission_id_fk` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 用户表 (自定义用户模型，继承 AbstractUser)
-- ========================================

CREATE TABLE IF NOT EXISTS `sys_user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `password` VARCHAR(128) NOT NULL,
    `last_login` DATETIME(6) DEFAULT NULL,
    `is_superuser` TINYINT(1) NOT NULL DEFAULT 0,
    `username` VARCHAR(150) NOT NULL,
    `first_name` VARCHAR(150) NOT NULL DEFAULT '',
    `last_name` VARCHAR(150) NOT NULL DEFAULT '',
    `email` VARCHAR(254) NOT NULL DEFAULT '',
    `is_staff` TINYINT(1) NOT NULL DEFAULT 0,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `date_joined` DATETIME(6) NOT NULL,
    `phone` VARCHAR(11) NOT NULL DEFAULT '',
    `company_name` VARCHAR(100) NOT NULL DEFAULT '',
    `role` VARCHAR(20) NOT NULL DEFAULT 'viewer',
    `avatar` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `sys_user_username_uniq` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户-组关联表
CREATE TABLE IF NOT EXISTS `sys_user_groups` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `group_id` INT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `sys_user_groups_user_id_group_id_uniq` (`user_id`, `group_id`),
    KEY `sys_user_groups_user_id_fk` (`user_id`),
    KEY `sys_user_groups_group_id_fk` (`group_id`),
    CONSTRAINT `sys_user_groups_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`),
    CONSTRAINT `sys_user_groups_group_id_fk` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户-权限关联表
CREATE TABLE IF NOT EXISTS `sys_user_user_permissions` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `permission_id` INT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `sys_user_user_permissions_user_id_permission_id_uniq` (`user_id`, `permission_id`),
    KEY `sys_user_user_permissions_user_id_fk` (`user_id`),
    KEY `sys_user_user_permissions_permission_id_fk` (`permission_id`),
    CONSTRAINT `sys_user_user_permissions_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`),
    CONSTRAINT `sys_user_user_permissions_permission_id_fk` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 业务表 - 合同管理
-- ========================================

-- 合同表
CREATE TABLE IF NOT EXISTS `biz_contract` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    `contract_no` VARCHAR(50) NOT NULL,
    `title` VARCHAR(200) NOT NULL,
    `client_name` VARCHAR(100) NOT NULL,
    `client_contact` VARCHAR(50) NOT NULL DEFAULT '',
    `product_type` VARCHAR(50) NOT NULL DEFAULT '',
    `amount` DECIMAL(15,2) NOT NULL,
    `currency` VARCHAR(10) NOT NULL DEFAULT 'CNY',
    `region` VARCHAR(50) NOT NULL DEFAULT '',
    `sign_date` DATE DEFAULT NULL,
    `start_date` DATE DEFAULT NULL,
    `end_date` DATE DEFAULT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'draft',
    `payment_status` VARCHAR(20) NOT NULL DEFAULT 'unpaid',
    `delivery_status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `salesperson` VARCHAR(50) NOT NULL DEFAULT '',
    `department` VARCHAR(50) NOT NULL DEFAULT '',
    `description` LONGTEXT NOT NULL,
    `attachments` JSON NOT NULL,
    `created_by_id` BIGINT DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `biz_contract_contract_no_uniq` (`contract_no`),
    KEY `biz_contract_is_deleted_idx` (`is_deleted`),
    KEY `biz_contract_created_by_id_fk` (`created_by_id`),
    CONSTRAINT `biz_contract_created_by_id_fk` FOREIGN KEY (`created_by_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 合同变更记录表
CREATE TABLE IF NOT EXISTS `biz_contract_change_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    `field_name` VARCHAR(50) NOT NULL,
    `old_value` LONGTEXT NOT NULL,
    `new_value` LONGTEXT NOT NULL,
    `contract_id` BIGINT NOT NULL,
    `changed_by_id` BIGINT DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `biz_contract_change_log_contract_id_fk` (`contract_id`),
    KEY `biz_contract_change_log_changed_by_id_fk` (`changed_by_id`),
    CONSTRAINT `biz_contract_change_log_contract_id_fk` FOREIGN KEY (`contract_id`) REFERENCES `biz_contract` (`id`) ON DELETE CASCADE,
    CONSTRAINT `biz_contract_change_log_changed_by_id_fk` FOREIGN KEY (`changed_by_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 付款计划表
CREATE TABLE IF NOT EXISTS `biz_payment_plan` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    `phase` VARCHAR(50) NOT NULL,
    `amount` DECIMAL(15,2) NOT NULL,
    `due_date` DATE NOT NULL,
    `paid_date` DATE DEFAULT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `remark` LONGTEXT NOT NULL,
    `contract_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    KEY `biz_payment_plan_contract_id_fk` (`contract_id`),
    CONSTRAINT `biz_payment_plan_contract_id_fk` FOREIGN KEY (`contract_id`) REFERENCES `biz_contract` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 业务表 - 数据分析
-- ========================================

-- 分析快照表
CREATE TABLE IF NOT EXISTS `analytics_snapshot` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    `date` DATE NOT NULL,
    `total_contracts` INT NOT NULL DEFAULT 0,
    `total_amount` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    `active_contracts` INT NOT NULL DEFAULT 0,
    `completed_contracts` INT NOT NULL DEFAULT 0,
    `new_contracts` INT NOT NULL DEFAULT 0,
    `new_amount` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    `region_data` JSON NOT NULL,
    `product_data` JSON NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `analytics_snapshot_date_uniq` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 业务表 - 系统管理
-- ========================================

-- 操作日志表
CREATE TABLE IF NOT EXISTS `sys_operation_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `ip_address` CHAR(39) DEFAULT NULL,
    `action` VARCHAR(20) NOT NULL,
    `target` VARCHAR(200) NOT NULL DEFAULT '',
    `detail` LONGTEXT NOT NULL,
    `method` VARCHAR(10) NOT NULL DEFAULT '',
    `path` VARCHAR(500) NOT NULL DEFAULT '',
    `status_code` INT DEFAULT NULL,
    `created_at` DATETIME(6) NOT NULL,
    `user_id` BIGINT DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `sys_operation_log_user_id_fk` (`user_id`),
    CONSTRAINT `sys_operation_log_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- SimpleJWT Token 黑名单表 (django-rest-framework-simplejwt)
-- ========================================

CREATE TABLE IF NOT EXISTS `token_blacklist_outstandingtoken` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT DEFAULT NULL,
    `jti` VARCHAR(255) NOT NULL,
    `token` LONGTEXT NOT NULL,
    `created_at` DATETIME(6) DEFAULT NULL,
    `expires_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `token_blacklist_outstandingtoken_jti_uniq` (`jti`),
    KEY `token_blacklist_outstandingtoken_user_id_fk` (`user_id`),
    CONSTRAINT `token_blacklist_outstandingtoken_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `token_blacklist_blacklistedtoken` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `blacklisted_at` DATETIME(6) NOT NULL,
    `token_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `token_blacklist_blacklistedtoken_token_id_uniq` (`token_id`),
    CONSTRAINT `token_blacklist_blacklistedtoken_token_id_fk` FOREIGN KEY (`token_id`) REFERENCES `token_blacklist_outstandingtoken` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
