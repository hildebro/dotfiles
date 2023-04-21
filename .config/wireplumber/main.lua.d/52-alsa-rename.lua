rule = {
  matches = {
    {
      { "node.name", "equals", "alsa_output.pci-0000_0b_00.4.analog-stereo" },
    },
  },
  apply_properties = {
    ["node.description"] = "Desktop Speakers",
  },
}

table.insert(alsa_monitor.rules,rule)

rule = {
  matches = {
    {
      { "node.name", "equals", "alsa_output.usb-GeneralPlus_USB_Audio_Device-00.analog-stereo" },
    },
  },
  apply_properties = {
    ["node.description"] = "Wired Headphones",
  },
}

table.insert(alsa_monitor.rules,rule)
