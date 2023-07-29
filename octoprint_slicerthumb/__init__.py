# coding=utf-8
from __future__ import absolute_import
from os import path, pardir
import socket

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
from octoprint.server import user_permission
from octoprint.events import Events

class SlicerthumbPlugin(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.SettingsPlugin,
                        octoprint.plugin.EventHandlerPlugin):

    def __init__(self):
        self.mqtt_basetopic = "octoprint/"
        self.mqtt_plugintopic = "slicerthumb"
        self.mqtttopic = ""
        self.plugins_basepath = "~/.octoprint/data"
        self.tumbnail_plugin_paths = ["prusaslicerthumbnails",
                                        "UltimakerFormatPackage"]

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            mqtt_basetopic = "",
            mqtt_plugintopic = "slicerthumb"
        )

    ##~~ StartupPlugin mixin
    def _get_basepath(self):
        datapath = self.get_plugin_data_folder()
        basepath = path.abspath(path.join(datapath, pardir))
        return basepath

    def on_startup(self, host, port):
        self.plugins_basepath = self._get_basepath()
        self._logger.debug(self.plugins_basepath)
        if self._settings.get(["mqtt_basetopic"]) == "":
            self._settings.set(["mqtt_basetopic"], self._settings.global_get(["plugins","mqtt","publish", "baseTopic"]))
            self._settings.save()
            
        self.mqtt_basetopic = self._settings.get(["mqtt_basetopic"])
        self.mqtt_plugintopic = self._settings.get(["mqtt_plugintopic"])
        self._logger.info("Slicerthumbnail will be published to: "+self.mqtt_basetopic+self.mqtt_plugintopic)

    def on_after_startup(self):
        self.link_mqtt()

    ##~~ EventHandlerplugin mixin

    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED:
            thumbnail_url = self.build_url(payload['name'])
            self._logger.debug(thumbnail_url)
            if (thumbnail_url != 'no_url'):
                try:
                    self.mqtt_publish(self.mqtt_basetopic+self.mqtt_plugintopic, thumbnail_url)
                    self._logger.info("Published message: "+thumbnail_url)
                except:
                    self._logger.Error("There was a problem publishing thumbnail URL")
            else:
                self._logger.info("Nothing to publish")


    def link_mqtt(self):
        self.mqtttopic = self.mqtt_basetopic+self.mqtt_plugintopic
        helpers = self._plugin_manager.get_helpers("mqtt", "mqtt_publish")
        if helpers:
            if "mqtt_publish" in helpers:
                self.mqtt_publish = helpers["mqtt_publish"]
                self._logger.debug("publish to MQTT is available")

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def build_url(self, gcodefile):
        thumbfile = gcodefile.replace('gcode', 'png')
        myip = self.get_ip()
        slicer = ""

        # Test if the thumbnailfile exists in one of the defined plugin folders
        for slicerPluginPath in self.tumbnail_plugin_paths:
            path_to_thumbnail = self.plugins_basepath+"/"+slicerPluginPath+"/"+thumbfile
            self._logger.debug(path_to_thumbnail)
            if path.isfile(path_to_thumbnail):
                self._logger.debug("Path Exists")
                slicer = slicerPluginPath
                break

        if slicer != "":
            self._logger.debug("thumbnail found in folder "+slicer)
            return "http://{ip}/plugin/{slicer}/thumbnail/{filename}".format(ip=myip, slicer = slicer, filename=thumbfile)
        else:
            self._logger.debug("thumbnail not found")
            return "no_url"

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "slicerthumb": {
                "displayName": "Slicerthumb Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "Wummeke",
                "repo": "slicerthumb",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/Wummeke/slicerthumb/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Slicerthumb Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SlicerthumbPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

