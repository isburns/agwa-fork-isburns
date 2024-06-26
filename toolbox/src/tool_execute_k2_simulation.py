# -*- coding: utf-8 -*-
import arcpy
import os
import sys
import pandas as pd
import glob
import subprocess
# from subprocess import Popen, PIPE
sys.path.append(os.path.dirname(__file__))


class ExecuteK2Simulation(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Step 9 - Execute K2 Simulation"
        self.description = ""
        self.canRunInBackground = False

    # noinspection PyPep8Naming
    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(displayName="AGWA Discretization",
                                 name="AGWA_Discretization",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input")
        discretization_list = []
        project = arcpy.mp.ArcGISProject("CURRENT")
        m = project.activeMap
        for lyr in m.listLayers():
            if lyr.isFeatureLayer:
                if lyr.supports("CONNECTIONPROPERTIES"):
                    cp_top = lyr.connectionProperties
                    # check if layer has a join, because the connection properties are nested below 'source' if so.
                    cp = cp_top.get('source')
                    if cp is None:
                        cp = cp_top
                    wf = cp.get("workspace_factory")
                    if wf == "File Geodatabase":
                        ci = cp.get("connection_info")
                        if ci:
                            workspace = ci.get("database")
                            if workspace:
                                meta_discretization_table = os.path.join(workspace, "metaDiscretization")
                                if arcpy.Exists(meta_discretization_table):
                                    dataset_name = cp["dataset"]
                                    discretization_name = dataset_name.replace("_elements", "")
                                    fields = ["DiscretizationName"]
                                    row = None
                                    expression = "{0} = '{1}'".format(
                                        arcpy.AddFieldDelimiters(workspace, "DiscretizationName"), discretization_name)
                                    with arcpy.da.SearchCursor(meta_discretization_table, fields, expression) as cursor:
                                        for row in cursor:
                                            discretization_name = row[0]
                                            discretization_list.append(discretization_name)

        param0.filter.list = discretization_list

        param1 = arcpy.Parameter(displayName="Simulation",
                                 name="Simulation",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input")

        param2 = arcpy.Parameter(displayName="Workspace",
                                 name="Workspace",
                                 datatype="GPString",
                                 parameterType="Derived",
                                 direction="Output")

        param3 = arcpy.Parameter(displayName="Delineation Name",
                                 name="Delineation_Name",
                                 datatype="GPString",
                                 parameterType="Derived",
                                 direction="Output")

        param4 = arcpy.Parameter(displayName="Debug messages",
                                 name="Debug",
                                 datatype="GPString",
                                 parameterType="Optional",
                                 direction="Input")

        param5 = arcpy.Parameter(displayName="Save Intermediate Outputs",
                                 name="Save_Intermediate_Outputs",
                                 datatype="GPBoolean",
                                 parameterType="Optional",
                                 direction="Input")
        param5.value = False

        params = [param0, param1, param2, param3, param4, param5]
        return params

    # noinspection PyPep8Naming
    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    # noinspection PyPep8Naming
    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        discretization_name = parameters[0].value
        workspace = ""
        if discretization_name:
            project = arcpy.mp.ArcGISProject("CURRENT")
            m = project.activeMap
            for lyr in m.listLayers():
                if lyr.isFeatureLayer:
                    if lyr.supports("CONNECTIONPROPERTIES"):
                        cp_top = lyr.connectionProperties
                        # check if layer has a join, because the connection properties are nested below 'source' if so.
                        cp = cp_top.get('source')
                        if cp is None:
                            cp = cp_top
                        wf = cp.get("workspace_factory")
                        if wf == "File Geodatabase":
                            dataset_name = cp["dataset"]
                            if dataset_name == discretization_name + "_elements":
                                ci = cp.get("connection_info")
                                if ci:
                                    workspace = ci.get("database")

        parameters[2].value = workspace
        workspace_directory = os.path.split(workspace)[0]

        # populate the available parameter files
        simulations_list = []
        if parameters[0].value:
            discretization_name = parameters[0].valueAsText

            meta_discretization_table = os.path.join(workspace, "metaDiscretization")
            if arcpy.Exists(meta_discretization_table):
                df_discretization = pd.DataFrame(arcpy.da.TableToNumPyArray(meta_discretization_table,
                                                                            ["DelineationName", "DiscretizationName"]))
                df_discretization_filtered = \
                    df_discretization[df_discretization.DiscretizationName == discretization_name]
                delineation_name = df_discretization_filtered.DelineationName.values[0]
                parameters[3].value = delineation_name

                simulations_path = os.path.join(workspace_directory, delineation_name, discretization_name,
                                                "simulations", "*")
                simulations_list = glob.glob(simulations_path)

        parameters[1].filter.list = simulations_list

        return

    # noinspection PyPep8Naming
    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # arcpy.AddMessage("Toolbox source: " + os.path.dirname(__file__))
        arcpy.AddMessage("Script source: " + __file__)
        discretization_par = parameters[0].valueAsText
        simulation_par = parameters[1].valueAsText
        workspace_par = parameters[2].valueAsText
        delineation_par = parameters[3].valueAsText

        workspace_directory = os.path.split(workspace_par)[0]
        k2_path = os.path.join(simulation_par, "k2.exe -b")

        # This executes the model, but the command window closes automatically without the opportunity to see the output
        # subprocess.Popen(k2_path, cwd=simulation_par)

        # This executes the model and keeps the command window open
        subprocess.Popen(["start", "cmd", "/k", k2_path], shell=True, cwd=simulation_par)

        # A failed attempt at executing the model and keeping the command window open until a key is pressed
        # process = subprocess.Popen(k2_path, cwd=simulation_par, stdin=subprocess.PIPE, text=True)
        # process.communicate("\n")

        return

    # noinspection PyPep8Naming
    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
