# Swarmconstraint Repository

Watch availability for one or more nodes in a Docker Swarm, and react to availability changes by enabling or disabling labels on other nodes.

## Background
Docker Swarm placement constraints are "hard" constraints. This means that if all nodes which satisfies constraints for a services goes down, that service goes down as well. The service will not be scheduled again before at least one node satisfies the placement constraints for that service.

## Use Case

You run a Docker Swarm across multiple data centers (DCs). You prefer a service to primarily run in one of the DCs, but are willing to accept different placements if the preferred DCs becomes unavailable.

This application will watch node availability. If the watched nodes becomes unavailable, the application will disable one
or more specified labels to ensure that constrained services will be scheduled.

## Example

Let's assume a 3 node Docker Swarm covering 3 DCs. We would like a certain service to run in DC1. We can achive this with a placement constraint set for that service :

    secondary!=true

This will ensure that the service only gets scheduled on nodes without the **secondary** label set to **true**.

### Nodes Overview

|DC   |Node |Labels          |
|-----|-----|----------------|
|DC1  |node1|                |
|DC2  |node2|secondary=true  |
|DC3  |node3|secondary=true  |

With the above nodes configuration, the service will only be scheduled on node1.       

### Usage

    user@node2:~$ swarmconstraint --watch node1 --toggle node2 --label secondary --prefix disabled

What happens with this command is that the application will monitor the availability of **node1**. Once node1 becomes unavailable, the application will toggle the label **secondary** on **node2**. This is done by simply prefixing the **secondary** label with **disabled**, so that the label becomes **disabled.secondary**.

Once **node1** becomes available again, the application will enable the **secondary** label by removing the **disabled** prefix. You need to manually any services which may have been scheduled on nodes during the time that the label was disabled.
