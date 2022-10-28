# pyROS
A Redis-based pure python alternative to ROS2

[Installation](#installation) |  [Usage](#usage) | [Advanced Topics](#advanced-topics) | [About](#about)

---
> **Warning** 
> This library is still in development, and has not been properly tested, use at your own risks
---

pyROS is an event-based publisher/subscriber communication framework, aimed at enabling fast development and prototying of event-driven applications. Those include robotics, simulation, and any other application operating on this ethos. It follows a very similar structure to the well established Robot Operating System (ROS), with an emphasis put on minimal development overhead and fast prototyping.

As such, the development of this library has been done according to the following ethos:

- **A pure-python implementation:** The goal of pyROS is not performance as much as it is fast and flexible prototyping. Python was as such selected, given its ease of use and accessibility.

- **An interface similar to that of ROS2:** Scripts developed using pyROS should be portable to ROS2 with minimal modifications if desired (given no pyROS-specific features are used, more on that later).

- **Minimal development overhead:** pyROS gets rid of all unnecessary steps when possible. There is no more need for compiling, messages definitions, packages etc.

- **Minimal dependencies:** To further reduce complexity, dependencies where kept to a minimum. The only major dependency being *Redis*,  and the *python-redis-lock* library.

- **Modular and expandable:** pyROS was coded to be easily expanded. New interfaces can easily be setup, allowing for testing new configurations and ideas.

*It should be noted that pyROS is also capable of communicating with ROS/ROS2. Bridges are under development and will be released soon.*

## Why Redis?
*"Redis is an in-memory data structure store, used as a distributed, in-memory key–value database, cache and message broker, with optional durability."*

Redis solves the issue of cross-process comunication, while ensuring performance and reliability in the exchange of information. It can furthermore be deployed on distibuted architecture, making it an interesting choice for scalability purposes.

# Installation
*Coming soon*
# Usage
With pyROS, any python class can be made a node capable of communicating with the communication layer. Similarly to ROS2, the class can inherit from pyROS's node class, which in turn gives it access to all pyROS methods. 

Alternatively a pyROS node can be created, which can then be passed around, and interfaced with as needs be.

*Coming soon*

## Core endpoints
To allow for emulating all behaviors desired, three core endpoints are necessary:
- The **publisher**: Used to push data to topics
- The **subscriber**: Used to monitor, retreive, and react to data being published on topics
- The **shared variable**: Used to store a single, cross-process value (somewhat similar to ROS's parameters)

All other behaviors can be achieved through combining the above (more in [custom endpoints](#custom-endpoints))

### Publisher
*Coming soon*
### Subscriber
*Coming soon*
### Shared_variable
*Coming soon*
## Custom endpoints
The three core endpoints can be combined to emulate most behaviors. pyROS makes it easy to build on those to achieve the desired behaviors. Currently, the following custom endpoints are being developed

### Behavior
- **Service:** Allows for request/response pattern

### Bridges
- **ROS publisher:** Bridge endpoint, allowing for sending messages through ROS
- **ROS subscriber:** Bridge endpoint, allowing for sending messages through ROS

# From pyROS to ROS2
*Coming soon*
# Advanced Topics
*Coming soon*
## Custom endpoints
*Coming soon*
# About
pyROS was developed as part of a **larger upcoming project**. Stay tunned for more! 
