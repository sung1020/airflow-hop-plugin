# -*- coding: utf-8 -*-
# Copyright 2022 Aneior Studio, SL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import gzip
import json
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

class XMLBuilder:
    """
    Builds an XML file to be sent through HTTP protocol
    """

    PIPE_INFO_POS = 0
    PIPE_PARAM_POS = 7
    WORKFLOW_PARAM_POS = 9

    def __init__(
                self,
                metastore_file,
                hop_config,
                project_config,
                environment_config = None):
        self.metastore_file = metastore_file
        self.hop_config = hop_config
        self.project_config = project_config
        self.environment_config = environment_config

    def get_workflow_xml(self, workflow_file) -> str:
        root = Element('workflow_configuration')
        workflow = ElementTree.parse(workflow_file)
        root.append(workflow.getroot())
        root.append(self.__get_workflow_execuion_config(workflow_file))
        root.append(self.__generate_element('metastore_json', self.__generate_metastore()))
        return ElementTree.tostring(root, encoding='unicode')

    def __get_workflow_execuion_config(self, workflow_file) -> Element:
        root = Element('workflow_execution_configuration')
        root.append(self.__get_workflow_parameters(workflow_file))
        root.append(self.__get_variables())
        root.append(self.__generate_element('run_configuration','local'))
        return root

    def __get_workflow_parameters(self, workflow_file):
        tree = ElementTree.parse(workflow_file)
        tree_root = tree.getroot()
        parameters = tree_root.findall('parameters')
        root = Element('parameters')
        for parameter in parameters[0]:
            new_param = Element('parameter')
            new_param.append(self.__generate_element('name',parameter[0].text))
            new_param.append(self.__generate_element('value',parameter[1].text))
            root.append(new_param)
        return root


    def get_pipeline_xml(self, pipeline_file, pipeline_config) -> str:
        root = Element('pipeline_configuration')
        pipeline = ElementTree.parse(pipeline_file)
        root.append(pipeline.getroot())
        root.append(self.__get_pipeline_execution_config(pipeline_config, pipeline_file))
        root.append(self.__generate_element('metastore_json', self.__generate_metastore()))
        return ElementTree.tostring(root, encoding='unicode')

    def __get_pipeline_execution_config(self, pipeline_config, pipeline_file) -> Element:
        root = Element('pipeline_execution_configuration')
        root.append(self.__get_pipe_parameters(pipeline_file))
        root.append(self.__get_variables(pipeline_config))
        root.append(self.__generate_element('run_configuration','local'))
        return root

    def __get_pipe_parameters(self, pipeline_file) -> Element:
        tree = ElementTree.parse(pipeline_file)
        tree_root = tree.getroot()
        parameters = tree_root[0].findall('parameters')
        root = Element('parameters')
        for parameter in parameters[0]:
            new_param = Element('parameter')
            new_param.append(self.__generate_element('name',parameter[0].text))
            new_param.append(self.__generate_element('value',parameter[1].text))
            root.append(new_param)
        return root

    def __get_variables(self, pipeline_config = None) -> Element:
        with open(self.hop_config, encoding='utf-8') as f:
            data = json.load(f)
        variables = data['variables']
        root = Element('variables')
        for variable in variables:
            new_variable = Element('variable')
            new_variable.append(self.__generate_element('name', variable['name']))
            new_variable.append(self.__generate_element('value', variable['value']))
            root.append(new_variable)

        if pipeline_config is not None:
            with open(pipeline_config, encoding='utf-8') as f:
                data = json.load(f)
            pipeline_vars = data['configurationVariables']
            for variable in pipeline_vars:
                new_variable = Element('variable')
                new_variable.append(self.__generate_element('name',variable['name']))
                new_variable.append(self.__generate_element('value',variable['value']))
                root.append(new_variable)

        with open(self.project_config, encoding='utf-8') as f:
            data = json.load(f)
        project_vars = data['config']['variables']
        for variable in project_vars:
            new_variable = Element('variable')
            new_variable.append(self.__generate_element('name',variable['name']))
            new_variable.append(self.__generate_element('value',variable['value']))
            root.append(new_variable)

        if self.environment_config is not None:
            with open(self.environment_config, encoding='utf-8') as f:
                data = json.load(f)
            environment_vars = data['variables']
            for variable in environment_vars:
                new_variable = Element('variable')
                new_variable.append(self.__generate_element('name', variable['name']))
                new_variable.append(self.__generate_element('value', variable['value']))
                root.append(new_variable)

        jdk_debug = Element('variable')
        jdk_debug.append(self.__generate_element('name','jdk.debug'))
        jdk_debug.append(self.__generate_element('value','release'))
        root.append(jdk_debug)
        return root

    def __generate_metastore(self) -> str:
        file = open(self.metastore_file, mode='br')
        content = file.read()
        file.close()
        metastore = gzip.compress(content)
        return base64.b64encode(metastore).decode('utf-8')

    def __generate_element(self, name:str, text = None) -> Element:
        element = Element(name)
        if text is not None:
            element.text = text
        return element
