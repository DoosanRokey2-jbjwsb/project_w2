from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='example_project',
            executable='customer_v4',
            name='customer_node',
            output='screen'
        ),
        Node(
            package='example_project',
            executable='kitchen_v4',
            name='kitchen_node',
            output='screen'
        )
    ])
