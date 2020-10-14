#!/usr/bin/python3

import argparse
import docker
import json
import logging
import re
import string
import time

class SwarmConstraint:

  def __init__(self, args):
    self.args = args
    self.initClient()

    self.logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)-25s  %(levelname)-8s  %(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)
    self.logger.setLevel(logging.DEBUG)

    if (not self.args['watch']):
      raise Exception('At least one node to watch must be provided.')

    if (not self.args['toggle']):
      raise Exception('At least one node to toggle must be provided.')

    if (not self.args['label']):
      raise Exception('At least one label must be provided.')

    if (not self.args['prefix']):
      raise Exception('A prefix must be provided.')

    self.logger.info('Watch {watch}.'.format(watch=','.join(self.args['watch'])))
    self.logger.info('Toggle the label(s) {labels} on {toggle}.'.format(labels=','.join(self.args['label']), toggle=','.join(self.args['toggle'])))
    self.logger.info('Prefix disabled labels with {prefix}.'.format(prefix=self.args['prefix']))

  def run(self):

    # Collect availability for watched nodes, and keep track of the collective
    # availability for all the watched nodes.
    nodes = self.getNodes()
    allWatchedNodesUnavailable = True
    for nodeId in nodes:
      watchNode = nodes[nodeId]
      if (not self.args['watch'] or watchNode['hostname'] not in self.args['watch']):
        continue

      if (self.isNodeAvailable(watchNode) == True):
        allWatchedNodesUnavailable = False
        break;

    if (allWatchedNodesUnavailable):
      self.logger.warn('All watched nodes are unavailable.')
    else:
      self.logger.debug('One or more watched nodes are available.')

    # Disable or enable labels depending on the collective availability for all
    # the watched nodes. 
    for nodeId in nodes:
      toggleNode = nodes[nodeId]
      if (self.args['toggle'] and toggleNode['hostname'] not in self.args['toggle']):
        continue

      if (allWatchedNodesUnavailable):
        self.disableLabels(toggleNode, self.args['label'], self.args['prefix'])
      else:
        self.enableLabels(toggleNode, self.args['label'], self.args['prefix'])

  def getSocket(self):
    return 'unix://var/run/docker.sock'

  def initClient(self):
    # Initialize the docker client.
    socket = self.getSocket()
    self.client = docker.DockerClient(base_url=socket)

  def getNodes(self):
    # Returns all nodes.
    allNodes = self.client.nodes.list();
    allNodesMap = {}
    for node in allNodes:
      allNodesMap[node.id] = {
        'id' : node.id,
        'available' :  True if node.attrs['Spec']['Availability'] == 'active' else False,
        'hostname': node.attrs['Description']['Hostname'],
        'role' : node.attrs['Spec']['Role'],
        'platform' : {
          'os' : node.attrs['Description']['Platform']['OS'],
          'arch' : node.attrs['Description']['Platform']['Architecture']
        },
        'labels' : node.attrs['Spec']['Labels'],
      }

    return allNodesMap

  def isNodeAvailable(self, node):
    return node['available']

  def disableLabels(self, node, labels, prefix):
    # Disable labels on a node by adding a prefix to each label. The node will only be
    # updated if at least one of the provided labels are currently enabled.
    matchingNode = next(iter(self.client.nodes.list(filters={'id':node['id']})), None)
    if (matchingNode is None):
      return

    spec = matchingNode.attrs['Spec']
    update = False

    for label in labels:
      if (label not in spec['Labels']):
        continue

      nodeLabelKey = label
      nodeLabelVal = spec['Labels'][nodeLabelKey]
      spec['Labels'].update(self.prefixNodeLabel(nodeLabelKey, nodeLabelVal, prefix))
      spec['Labels'].pop(nodeLabelKey, None)
      update = True

      self.logger.info('Disabling the label "{key}={val} on {node}".'.format(key=nodeLabelKey, val=nodeLabelVal, node=node['id']))

    if (update):
      matchingNode.update(spec)
      return True
    else:
      return False

  def enableLabels(self, node, labels, prefix):
    # Enable labels on a node by removing the prefix from each label. The node will only be 
    # updated if at least one of the provided labels are currently disabled.
    matchingNode = next(iter(self.client.nodes.list(filters={'id':node['id']})), None)
    if (matchingNode is None):
      return

    spec = matchingNode.attrs['Spec']
    update = False

    for label in labels:
      label = self.prefixLabel(label, prefix)
      if (label not in spec['Labels']):
        continue

      nodeLabelKey = label
      nodeLabelVal = spec['Labels'][nodeLabelKey]
      spec['Labels'].update(self.unPrefixNodeLabel(nodeLabelKey, nodeLabelVal, prefix))
      spec['Labels'].pop(nodeLabelKey, None)
      update = True

      self.logger.info('Enabling the label "{key}={val} on {node}".'.format(key=nodeLabelKey, val=nodeLabelVal, node=node['id']))

    if (update):
      matchingNode.update(spec)
      return True
    else:
      return False

  def prefixLabel(self, label, prefix):
    # Split and prefix a label into a dictionary holding the prefixed key and the value separately.
    return '{prefix}.{key}'.format(prefix=prefix, key=label)

  def isNodeLabelPrefixed(self, key, prefix):
    # Evaluates if a node label is prefixed
    return True if key.find(prefix) > -1 else False;

  def prefixNodeLabel(self, key, val, prefix):
    # Prefix a node label.
    label = {'{prefix}.{key}'.format(prefix=prefix,key=key) : '{val}'.format(val=val)}
    return label

  def unPrefixNodeLabel(self, key, val, prefix):
    # Remove prefix from a node label.
    key = key.replace('{prefix}.'.format(prefix=prefix), '')
    label = {'{key}'.format(prefix=prefix,key=key) : '{val}'.format(val=val)}
    return label

class FromFileAction(argparse.Action):

  def __init__(self, option_strings, dest, nargs=None, **kwargs):
    super(FromFileAction, self).__init__(option_strings, dest, **kwargs)

  def __call__(self, parser, namespace, path, option_string=None):
    if (path):
      data = None
      with open(path) as f:
        data = json.load(f)

      if (data is None):
        return

      if ('watch' in data):
        namespace.watch += data['watch']

      if (data['toggle']):
        namespace.toggle += data['toggle']

      if ('label' in data):
        namespace.label += data['label']

    return

def main():
  parser = argparse.ArgumentParser(description='Toggles one or more constraints depending on node availability')
  parser.add_argument('--watch', metavar='watch', action='append', default=[], help='A node which availability is to be watched.')
  parser.add_argument('--toggle', metavar='toggle', action='append', default=[], help='A node for which constraints are to be toggled. Defaults to all nodes.')
  parser.add_argument('--label', metavar='label', action='append', default=[], help='A label which is to be toggled according to availability for watched nodes.')
  parser.add_argument('--prefix', metavar='prefix', default='disabled',  help='The prefix to use for disabled labels. Defaults to "disabled".')
  parser.add_argument('fromFile', action=FromFileAction, help='A file which holds configurations.')

  args = vars(parser.parse_args())
  se = SwarmConstraint(args)

  while(True):
    try:
      se.run()
      time.sleep(10)
    except KeyboardInterrupt:
      break
    except Exception as err:
      print(err)
      break

if __name__ == '__main__':
  main()

