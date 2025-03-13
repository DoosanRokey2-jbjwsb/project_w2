from setuptools import setup

package_name = 'example_project'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # launch 파일은 한 위치에만 설치되도록 수정
        ('share/' + package_name + '/launch', ['launch/example.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@email.com',
    description='Example project',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'customer_v4 = example_project.customer_v4:main',
            'kitchen_v4 = example_project.kitchen_v4:main',
        ],
    },
)
