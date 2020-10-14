# Swarmconstraint

Watch availability for one or more nodes in a Docker Swarm, and react to availability changes by enabling or disabling node labels.

## Background

Docker Swarm placement constraints are "hard" constraints. This means that if all nodes which satisfies constraints for a service go down, that service goes down as well. The service will not be scheduled again before at least one node satisfies the placement constraints for that service.

## Use Case

You run a Docker Swarm across multiple data centers (DCs). You prefer a service to primarily run in one of the DCs, but are willing to accept different placements if the preferred DC becomes unavailable.

This application will watch node availability. If the watched nodes becomes unavailable, the application will disable one
or more specified labels on one or more specified nodes to ensure that constrained services will be scheduled.

## Example

Let us assume a Docker Swarm covering 3 DCs. We would like a certain service to run in DC1. We can achive this with a placement constraint set for that service :

    secondary!=true

This will ensure that the service only gets scheduled on nodes where the **secondary** label is not set to **true**.

### Nodes Overview

|DC   |Node        |Labels          |
|-----|------------|----------------|
|DC1  |node1, node4|                |
|DC2  |node2       |secondary=true  |
|DC3  |node3       |secondary=true  |

With the above nodes configuration, the service will only be scheduled on node1 and node4.

### Usage

    user@node2:~$ swarmconstraint --watch node1 --watch node4 --label secondary --toggle node2 --prefix disabled

What happens with this command is that the application will monitor the availability of **node1** and **node4**. Once both node1 AND node4 becomes unavailable, the application will disable the label **secondary** on **node2**. This is done by simply prefixing the **secondary** label with **disabled**, so that the label becomes **disabled.secondary**.

Once **node1** AND **node4** becomes available again, the application will enable the **secondary** label by removing the **disabled** prefix. You need to manually re-balance services which may have been scheduled on nodes during the time that the label was disabled.

In the above setup, you would likely run the this application on **node2** and **node3** - and have each of these two nodes to update it's own label according to the availability of **node1** and **node4**.

### Arguments

    swarmconstraint --watch node1 --watch node4 --label secondary --toggle node2 /opt/swarmconstraint/config.json

*All arguments may be used multiple times, except for prefix which may only be used once.*

**watch** : the nodes which the application is to watch availability for. 
**label** : the node labels which the application is to disable / enable when the watched nodes become unavailable. 
**toggle** : the nodes on which the provided labels are to be enabled or disabled depending on availability
**prefix** : the prefix which is to be prepended to labels when disabled.

You may also provide the path to a configuration file. This is a JSON file expecting the following format.

    {
      "watch": ["node1", "node4"],
      "toggle": ["node2"],
      "label": ["secondary"],
      "prefix": "disable"
    }
    
