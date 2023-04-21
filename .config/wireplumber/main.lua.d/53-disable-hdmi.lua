rule = {
  matches = {
    {
      { "node.name", "equals", "alsa_output.pci-0000_09_00.1.hdmi-stereo-extra3" },
    },
  },
  apply_properties = {
    ["node.disabled"] = true,
  },
}

table.insert(alsa_monitor.rules,rule)

