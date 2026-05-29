from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'single_robot'


def collect_tree(src_dir):
    """Recursively collect files under src_dir into (install_dir, [files]) tuples."""
    entries = []
    for dirpath, _, filenames in os.walk(src_dir):
        files = [os.path.join(dirpath, f) for f in filenames]
        if files:
            install_dir = os.path.join('share', package_name, dirpath)
            entries.append((install_dir, files))
    return entries


setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ] + collect_tree('models') + collect_tree('worlds'),
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jaqueline',
    maintainer_email='jaqueline.machida@smail.inf.h-brs.de',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'collision_avoidance = single_robot.collision_avoidance:main',
            'wall_follower = single_robot.wall_follower:main',
            'vacuum_cleaner = single_robot.vacuum_cleaner:main',
        ],
    },
)
