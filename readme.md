# ⚙️ IsoEngine

<img title="" src="https://i.imgur.com/xJ3kEvR.png" alt="Screenshot 2024-06-16 233743.png" data-align="center">

### ✨ Main features:

- 🗺️ **Dynamic world generation** using `Perlin noise`.

- 🧊 3D World based on 2D graphics (2.5D Isometric)

- ⛏️ Terraforming.

- 🌟 Particles.

- 🧭 **Pathfinding algorithm**.

---

### 📦 Installation:

Download Python: https://www.python.org/downloads/

Install required libraries: 

```bash
(cd to project's directory)
pip install -r requirements.txt
```

Run project:

```bash
py main.py [options here]
// or
python3 main.py [options here]
```

---

### 🛠️ Startup options:

| **OPTION**     | **DESCRIPTION**                                                                              |
|:-------------- | -------------------------------------------------------------------------------------------- |
| `--no-save`    | Do not apply any saved changes from save file and don't save upcoming changes.               |
| `--clear-save` | Removes save file.                                                                           |
| `@seed`        | *Replace "seed" with an value.* Sets custom seed for world generation. (Replaces save file!) |
| `--help`       | Display basic help command with all options.                                                 |

---

### 🎛️ Controls:

##### 🖱️ Mouse:

- **Left button**: Destroy highlighted block.

- **Right button**: Place selected block.

- **Middle button**: Move to highlighted block using path finding algorithm.

##### ⌨️ Keyboard:

* **WSAD**: Move character.

* Space: Jump (max 3 blocks.)

---

### 🚀 FPS boost:

Standard `pygame` library is not well optimized and it can be replaced with the Community Edition which gives around 10 FPS boost.

```bash
pip uninstall pygame
pip install pygame-ce
```

---

### 💥 Known issues:

1. Sometimes Perlin noise height map generated for an chunk is drastically different than one generated for neighbor chunk (they don't transition smoothly).

---

### 💡 Some solutions explanation.

##### 🌱 Seed based world generation.

To generate height map I have used the `Perlin Noise` algorithm which creates smooth noise values which are then normalized for easier use in future. It's biggest advantage is the fact that it is **seed based** and it can generate noise value for given X, Y coordinate. Value for each `i, j` world column in `x, y` chunk is generated like this:

$`
\text{HeightMap}[i][j] = \text{noise}\left(\frac{\text{size} \times \text{chunk}_y + i}{\text{size}}, \frac{\text{size} \times \text{chunk}_x + j}{\text{size}}\right)
`$

where `noise(y, x)` returns value from Perlin map, `size` is chunk size (`16`) and `i, j ∈ [0, size-1]` 

Calling this formula for every `i, j` combination results in entire 2 dimensional array of height values in `x, y` chunk containing values in range `[-0.5, 0.5]`.

Real height (`Z` level) is determined using linear interpolation function which converts numbers from range `[-0.5, 0.5]` to integers in range `[1, MAX_HEIGHT//1.5]`. Then, according to the hardcoded map I place selected blocks on each level.

To avoid difference in water's height, after generating world I check for gaps in water and fill them. If empty block has water as a neighbor on the same Z level, it turns into water changing it's empty neighbors as well.

Python's standard `random` library can produce **seed based values** by calling `random.seed(SEED_VALUE)` so every time world generated using pseudo-randomness **will be the same**. I use random number generation for: 

1. Choosing random texture for each voxel.

2. Randomly placing environment objects like flowers.

##### 🚄 Rendering optimization.

Rendering is the most resource expensive task as it is called every frame, so even small change can have big impact on performance. 

**Rendering only visible voxels.**

The classical problem in rendering 3D objects is hiding invisible faces. In the 2.5D - isometric world there are only 2D objects, so I don't have to worry about faces specifically, but entire objects instead. There is no sense in rendering hundreds of voxels that will be hidden below other voxels nearer to the camera and in fact, the most of the voxels are hidden. That's why before beginning processing each voxel I must check if it is really visible for the camera. To do this I simply check if there is any voxel: above, on the left and on the right side.

**Skip useless iterations.**
To render every voxel, I must iterate over each voxel in the the 3 dimensional array. World iteration pseudo code:

```text
FOR z_row IN chunk:
  FOR y_row IN z_row:
    FOR voxel IN y_row:
      process voxel...
      shade voxel..
      render voxel...
```

Nesting three `for` loops and processing every value inside is really hard on resources, so skipping single iteration on the first or second level results in skipping up to `256` iterations. That's why each chunk generates `skip_heights` map which contains heights values where are no voxels placed. Since naturally generated world has voxels on Z level in range `[1, 13]` (*13 is result of MAX_HEIGHT//1.5*) I can already skip 7 levels each of 256 values! Before iterating over an `y_row` I also check if it isn't blank to save additional resources.

**Rendering objects only if they are in viewport.**
Clouds in the background are spawned out of the screen and are flying through it to disappear again on the other side of the screen. It allows me to randomly scale them and apply random speed to each of them. To avoid rendering cloud that is not in the viewport I simply check if it's leftmost pixel's position is less than screen width and if it's rightmost pixel's position is greater than 0.

##### 💾 Difference saves.

Entire map generated with default settings has `32x32` (*update: chunks limit has been removed!*) chunks, each of `16x16x20` voxels which gives `5,242,880` in total. File containing information about each voxel's state would be extremely big. Remember that the world generation is **seed based** and generating world with an seed will always give the same result. That's why instead of having to save naturally generated voxels I only save the **difference between naturally generated world and changes made by user** for each chunk that has been updated.

The difference from save file is applied during the chunk generation process which is exactly the same as in the first time generation. After that, I check for all changes made in that exact chunk and replace original voxels with those placed by user during another session. 

##### 🧭 Pathfinding algorithm.

Creating 2D pathfinding algorithm is pretty simple. 3D pathfinder is much more complex as it has to handle Z level difference between blocks. Algorithm is aware of possibility to jump or fall to lower level.

When user requests pathfinder's move using MMB, new `PathFinder` object is created. It contains information about: player's current position, destination and world object.

The algorithm operates on nodes. Each node contains:

1. It's world position (X, Y, Z).

2. Parent node.

3. Information how to move from parent's node to this node (type of move and angle direction).

4. Children nodes (next position player can move from this node).

When algorithm starts, it generates map of every possible position player can get to starting from the node with player's current position. It checks all possible moves in N, E, S, W direction from the node (including jumping and falling). After generating each node, it's distance to the destination position is checked and node with the smallest distance is saved as a backup node (if it is impossible to get to the destination). All nodes leading to the destination position are saved in a list. When every node has checked it's children positions, the cheapest trace is chosen. Cost of trace means amount of moves from the current position to the destination. If there is no node leading to the requested destination, backup node is used.

To generate sequence of moves from the node, I save movement instructions from the parent node in a array and continue to the grandparent and so on. After gathering instructions from each node, the array is reversed, so the first instruction leads from the current position to next in the sequence. Moves sequence is executed using the timed events (*check explanation below*).

##### ⏱️ Events, timed events, callbacks.

Some jobs in the code must be executed with some timeout to appear as smooth. For example: chunk loading animation, particles, pathfinder moves. That's why I created the `EventLoop` object containing `CallEvent` objects. Event loop keeps time-outed callbacks and if requested, executes all awaiting jobs. The `CallEvent` object contains: function to be called, it's parameters and time that it should be called.

There are three categories of loops:

- `main_loop`: contains falling steps and particles.

- `anim_loop`: events in this loop are pushing animation progress.

- `move_loop`: used for executing pathfinder's move instructions. 

`EventLoop` object allows me to clear all tasks waiting to be executed. It is very helpful in situation when I need to stop executing sequence in the middle of it. For example remove particles after changing chunk or breaking pathfinder moves sequence when user interrupts it with their manual move.



