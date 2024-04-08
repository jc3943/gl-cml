resource "fmc_access_policies" "access_policy" {
    name = "dcloud-accessPolicy"
    default_action = "permit"
}

resource "fmc_access_policies_category" "category" {
    name                  = "test-category"
    access_policy_id     = fmc_access_policies.access_policy.id
}

resource "fmc_access_rules" "access_rule_dbAdmins" {
    acp = fmc_access_policies.access_policy.id
    name = "DB Admins"
    category = "test-category"
    action = "monitor"
    enabled = true
    enable_syslog = false
    send_events_to_fmc = true
    log_files = false
    log_end = true
}

resource "fmc_access_rules" "access_rule_urlMon" {
    acp = fmc_access_policies.access_policy.id
    section = "mandatory"
    name = "URL Monitor"
    action = "monitor"
    enabled = true
    enable_syslog = false
    #syslog_severity = "alert"
    send_events_to_fmc = true
    log_files = false
    log_end = true
}

resource "fmc_access_rules" "access_rule_threatInspect" {
    acp = fmc_access_policies.access_policy.id
    section = "mandatory"
    name = "Threat Inspection"
    action = "allow"
    enabled = true
    enable_syslog = false
    #syslog_severity = "alert"
    send_events_to_fmc = true
    log_files = false
    log_end = true
}

resource "fmc_devices" "dcloud_ftd" {
    name = var.fmc_ftd1_name
    hostname = var.fmc_ftd1
    regkey = var.fmc_regkey
    type = "Device"
    access_policy {
        id = fmc_access_policies.access_policy.id
        type = fmc_access_policies.access_policy.type
    }
}

resource "fmc_security_zone" "inside_intf" {
  name          = "INSIDE_INTF"
  interface_mode = "ROUTED"
}

resource "fmc_security_zone" "outside_intf" {
  name          = "OUTSIDE_INTF"
  interface_mode = "ROUTED"
}

resource "fmc_security_zone" "dmz_intf" {
  name          = "DMZ_INTF"
  interface_mode = "ROUTED"
}

#THE FOLLOWING INTERFACE RESOURCES REFERENCE A HARD-CODE VALUE FOR PHYSICAL_INTERFACE_ID DUE TO A BUG THAT CRASHES PROVIDER ACQUIRING IT DYNAMICALLY.  TO BE RESOLVED
resource "fmc_device_physical_interfaces" "gig0_intf" {
    name = "GigabitEthernet0/0"
     device_id = fmc_devices.dcloud_ftd.id
     physical_interface_id = "00505697-B8D7-0ed3-0000-124554054330"
     security_zone_id = fmc_security_zone.inside_intf.id
     if_name = "inside"
     description = "inside zone interface"
     mtu = 1500
     mode = "NONE"
     ipv4_static_address = "1.1.1.1"
     ipv4_static_netmask = 24
     ipv4_dhcp_enabled = "false"
}

resource "fmc_device_physical_interfaces" "gig1_intf" {
    name = "GigabitEthernet0/1"
     device_id = fmc_devices.dcloud_ftd.id
     physical_interface_id = "00505697-B8D7-0ed3-0000-124554054331"
     security_zone_id = fmc_security_zone.outside_intf.id
     if_name = "outside"
     description = "outside zone interface"
     mtu = 1500
     mode = "NONE"
     ipv4_static_address = "2.2.2.1"
     ipv4_static_netmask = 24
     ipv4_dhcp_enabled = "false"
}

resource "fmc_device_physical_interfaces" "gig2_intf" {
    name = "GigabitEthernet0/2"
     device_id = fmc_devices.dcloud_ftd.id
     physical_interface_id = "00505697-B8D7-0ed3-0000-124554054332"
     security_zone_id = fmc_security_zone.dmz_intf.id
     if_name = "dmz"
     description = "dmz zone interface"
     mtu = 1500
     mode = "NONE"
     ipv4_static_address = "3.3.3.1"
     ipv4_static_netmask = 24
     ipv4_dhcp_enabled = "false"
}

resource "fmc_ftd_deploy" "ftd" {
    device = fmc_devices.dcloud_ftd.id
    ignore_warning = true
    force_deploy = true
}