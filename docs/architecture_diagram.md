```md
+----------------+       UART        +----------------------+
|  STM32F767     |  <------------->  |  Raspberry Pi 5     |
|  Bus Node      |                   |  Central Controller |
+----------------+                   +----------------------+
        |                                        |
        | Event Engine                           | Packet Parser
        | State Machine                          | Logger
        | Checksum Generator                     | Validator
```