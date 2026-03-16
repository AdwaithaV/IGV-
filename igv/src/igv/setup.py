from setuptools import find_packages, setup

package_name = 'igv'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='raju',
    maintainer_email='raju@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'camera_node = igv.camera:main',
            'remap_scan=igv.scan_remap:main',
            'path=igv.stage_1:main',
            # 'odom_node = igv.odometry:main',
            'terrian=igv.terrian_detection:main',
            'fusion=igv.ekf:main',
            'velocity_tune=igv.behaivour:main',
        ],
    },
)
