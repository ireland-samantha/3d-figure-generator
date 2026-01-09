# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-08

### Added

- Initial release
- Figure generation with anatomically-accurate proportions
- Built-in presets: `female_adult`, `male_adult`, `child`, `heroic`
- Pose options: `apose`, `tpose`, `relaxed`, custom angles
- Multiple backend support: trimesh, Open3D, numpy-stl
- Export to GLB, GLTF, OBJ, STL, PLY, DAE, OFF formats
- JSON configuration for custom proportions
- Command-line interface with full feature access
- Python API for programmatic use
- Comprehensive test suite
- Full documentation

### Body Parts

- Head (sphere)
- Neck (cylinder)
- Ribcage (box)
- Breasts (spheres, optional)
- Abdomen (cylinder)
- Pelvis (box)
- Glutes (spheres)
- Upper arms (cylinders)
- Forearms (cylinders)
- Hands (boxes)
- Thighs (cylinders)
- Calves (cylinders)
- Feet (boxes)
