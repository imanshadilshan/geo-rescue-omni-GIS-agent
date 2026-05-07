# Complete GIS Project Guide - Explained Simply! 🗺️

## Welcome! Let's Learn About Our Amazing GIS Project Together!

Hey there, friend! Imagine you're playing with maps and trying to help people during emergencies. That's exactly what our GIS project does! Let me explain everything in a way that's super easy to understand.

---

## Table of Contents

1. [What is GIS? 🗺️](#what-is-gis)
2. [What is JSON and GeoJSON? 📋](#what-is-json-and-geojson)
3. [Our Project's Mission 🚀](#our-projects-mission)
4. [The Magic Tools We Built 🛠️](#the-magic-tools-we-built)
5. [How Everything Works Together 🔄](#how-everything-works-together)
6. [Using Our Tools 📚](#using-our-tools)

---

## What is GIS? 🗺️

### Simple Explanation

GIS stands for "Geographic Information System." Think of it like this:

Imagine you have a **super smart digital map**. But it's not just any map. It's a map that knows TONS of information about every location on Earth. It can tell you:

- Where the roads are
- Where buildings are located
- What areas are flooded with water
- The best route to take from one place to another
- Which roads are blocked or broken

A GIS is like having a computer brain that understands maps and can answer questions about the real world by looking at data about locations and places.

### Why is GIS Awesome?

Without GIS: If there's a flood, someone has to manually check every single road on paper to see which ones are blocked. That takes HOURS and is super boring!

With GIS: The computer instantly tells you which roads are flooded, which roads are safe, and what the best route is to help people. It takes SECONDS!

### Our Specific Project

Our project uses GIS to help during **disaster emergencies** like floods. Here's what it does:

1. **Downloads satellite pictures** from space (real photos of Earth!)
2. **Gets all the roads** from a huge map database
3. **Detects which roads are blocked** by water or damage
4. **Plans safe routes** for rescue people to drive
5. **Saves all this information** in a format computers can use easily

---

## What is JSON and GeoJSON? 📋

### Understanding JSON First

JSON stands for "JavaScript Object Notation." But don't let the fancy name scare you! It's actually super simple.

JSON is just a **way to organize and write information** that computers can understand easily. It's like writing a list or a note, but in a very organized way that follows specific rules.

#### Simple JSON Example

Imagine you want to write information about your friend. You could write it like this:

**Bad way (messy):**

```
My friend is named Alice. She is 10 years old. She likes pizza.
```

**Good way (JSON):**

```json
{
  "name": "Alice",
  "age": 10,
  "favorites": ["pizza", "chocolate", "cats"]
}
```

The JSON way is better because:

- It's organized and easy to read
- Computers can understand it perfectly
- It follows a clear pattern with `{}` and `[]`

#### JSON Format Rules

In JSON, we use:

- **`{}`** - curly brackets to contain information (like a container)
- **`[]`** - square brackets to make lists
- **`"key": value`** - pairs of information (name and value)

#### Bigger JSON Example

Let's say we want to store information about three roads in a city:

```json
{
  "city": "Colombo, Sri Lanka",
  "roads": [
    {
      "name": "Galle Road",
      "length_meters": 5000,
      "type": "highway",
      "blocked": false
    },
    {
      "name": "Colombo Road",
      "length_meters": 3200,
      "type": "main_street",
      "blocked": true
    },
    {
      "name": "Beach Road",
      "length_meters": 4100,
      "type": "secondary_road",
      "blocked": false
    }
  ]
}
```

See how organized that is? The computer can easily understand:

- There are roads in Colombo
- There are 3 roads listed
- Each road has a name, length, type, and whether it's blocked

### Now Let's Talk About GeoJSON! 🗺️

GeoJSON is a special type of JSON that includes **geographical information**. In other words, it's JSON, but with superpowers for maps!

GeoJSON is used to store **location data** in a standard format. It tells computers:

- Where things are located on Earth (coordinates)
- What shape they are (is it a point, a line, or a polygon?)
- What information about that location

#### Why Do We Need GeoJSON?

Imagine you want to draw on a map:

- A **point** (like marking a specific location) - example: "There's a hospital here at coordinates X, Y"
- A **line** (like drawing a path or road) - example: "The road goes from point A to point B"
- A **polygon** (like drawing a filled area) - example: "The flood covers this entire area"

Regular JSON doesn't know how to handle map shapes. **GeoJSON does!**

#### GeoJSON Example: A Simple Point

Let's say we want to mark the location of a hospital on a map:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [80.7789, 6.9271]
  },
  "properties": {
    "name": "Colombo General Hospital",
    "services": "Emergency, Surgery, Trauma"
  }
}
```

Let me break this down:

- **`"type": "Feature"`** - This is a single item (like one thing on the map)
- **`"geometry"`** - This describes the shape and location
- **`"type": "Point"`** - It's a single dot on the map (not a line or area)
- **`"coordinates": [80.7789, 6.9271]`** - These numbers tell the computer WHERE on Earth this is! (longitude and latitude)
- **`"properties"`** - This is extra information ABOUT that location

#### GeoJSON Example: A Line (Road)

Now let's mark a road. A road is made of multiple points connected together, so we use a **LineString**:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [80.7789, 6.9271],
      [80.78, 6.928],
      [80.782, 6.93]
    ]
  },
  "properties": {
    "name": "Galle Road",
    "length_meters": 5000,
    "road_type": "highway",
    "blocked": false
  }
}
```

This says: "There's a road that goes through these three coordinates, and its name is Galle Road."

#### GeoJSON Example: A Polygon (Flooded Area)

Finally, let's mark an area that's flooded. This is a shape with an inside and an outside, so we use a **Polygon**:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [80.75, 6.9],
        [80.85, 6.9],
        [80.85, 7.0],
        [80.75, 7.0],
        [80.75, 6.9]
      ]
    ]
  },
  "properties": {
    "name": "Flood Zone A",
    "severity": "high",
    "affected_people": 500
  }
}
```

Notice the coordinates form a rectangle (they come back to the starting point to close the shape). This tells us the area that's underwater.

#### JSON vs GeoJSON - The Simple Difference

| Aspect          | Regular JSON           | GeoJSON                               |
| --------------- | ---------------------- | ------------------------------------- |
| **Purpose**     | Store any kind of data | Store location data specifically      |
| **Coordinates** | No special format      | Uses [longitude, latitude] pairs      |
| **Shapes**      | No shapes, just text   | Can represent Points, Lines, Polygons |
| **Best For**    | Lists, names, numbers  | Maps and geographical information     |

---

## Our Project's Mission 🚀

### What Problem Are We Solving?

During disasters like **floods**, cities get very chaotic. People need to get to safety, and rescue workers need to help others. But **some roads are blocked by water**, and nobody can drive on them!

**The Problem:**

- Without our system: Someone has to manually check each road to see if it's safe
- Takes hours or days
- People get stuck or can't get help
- Rescue workers waste time going the wrong way

**Our Solution:**

- Our system automatically detects blocked roads
- Finds safe routes instantly
- Tells rescue workers exactly where to go
- Saves lives and time!

### How Our Project Helps

Our project is like a **helpful robot friend** that does 5 amazing things:

1. **Looks at satellite pictures** from space to see where there's water
2. **Gets all the road information** from a big map database (OpenStreetMap)
3. **Compares the roads with the water** to see which roads are blocked
4. **Finds the best safe route** between two places
5. **Tells everyone where it is** by saving the information in a format anyone can use

---

## The Magic Tools We Built 🛠️

### Tool #1: Sentinel-2 Satellite Image Downloader 📡

**What It Does:**
This tool gets real satellite pictures from space! Specifically, it downloads images from a space satellite called Sentinel-2 that the European Space Agency launched.

**Simple Explanation:**
Imagine you have a camera in space that takes pictures of Earth every day. This tool asks that camera for a picture of Colombo, Sri Lanka, and it downloads it to your computer!

**The Details:**

- **Satellite:** Sentinel-2 (a real satellite in space!)
- **Location:** Colombo, Sri Lanka
- **Image Type:** RGB photo (like a normal color photo you take on your phone)
- **Resolution:** 10 meters (each pixel represents a 10-meter square on Earth)
- **Bands Used:** B04 (red), B03 (green), B02 (blue)

**Why These Bands?**
Satellites don't just take regular photos. They take pictures in different "colors" of light. Some light is visible (what we see), and some is invisible (like infrared). We picked three specific bands that combine to make a normal-looking color photo!

**What It Saves:**

- A PNG image file showing Colombo from space
- Shows buildings, water, roads, everything!

**Python File:** `download_sentinel2_rgb.py`

**Code Example:**

```python
from gis_tools.download_sentinel2_rgb import download_sentinel2_rgb

# Download satellite image of Colombo
image_path = download_sentinel2_rgb()
```

---

### Tool #2: OpenStreetMap Road Network Downloader 🛣️

**What It Does:**
This tool downloads ALL the roads in Colombo from a giant map database called OpenStreetMap. It's like asking Wikipedia for every single road in the city!

**Simple Explanation:**
Imagine you have a super detailed map of the city showing every single street, highway, and small road. This tool downloads that exact information!

**The Details:**

- **Source:** OpenStreetMap (a free, open database of the world)
- **Network Type:** Drivable roads (roads that cars can use)
- **Format:** Graph structure (which means roads connected at intersections)
- **Output:** Both individual nodes (intersection points) and edges (road segments)

**Graph? What's That?**
Think of a graph like this:

- **Nodes** are intersections (where roads meet)
- **Edges** are road segments (the road between two intersections)
- Together, they form a network that represents the entire road system!

**What It Saves:**

- `colombo_road_network.geojson` - All the road segments
- `colombo_road_nodes.geojson` - All the intersections
- `colombo_road_network_graph.graphml` - The network structure in a special format

**Python File:** `road_network.py`

**Code Example:**

```python
from gis_tools.road_network import download_and_process_road_network

# Download all roads in Colombo
edges_path, nodes_path, graph_path = download_and_process_road_network()
```

---

### Tool #3: Flood Overlay and Impact Analysis 💧

**What It Does:**
This tool compares the satellite images with the road network to figure out which roads are blocked by water!

**Simple Explanation:**
Imagine you overlay a transparent sheet with roads drawn on it on top of a satellite photo. Then you see exactly which roads pass through water. That's what this tool does with computers!

**The Details:**

- **Creates:** A circular flood zone (represents the affected area)
- **Compares:** The flood zone with all the roads
- **Identifies:** Which roads intersect with water
- **Classifies:** Roads as "fully blocked" or "partially blocked"

**The Process:**

1. Load the road network data (all roads)
2. Load/create the flood polygon (the area with water)
3. Use spatial overlay (compare shapes)
4. Find intersections (where roads cross water)
5. Mark those roads as blocked

**What It Saves:**

- `blocked_roads_flood.geojson` - All the blocked road segments
- `flood_polygon.geojson` - The flood zone boundary
- Statistics about how many roads are affected

**Python File:** `flood_overlay.py`

**Code Example:**

```python
from gis_tools.flood_overlay import analyze_flood_impact

# Analyze which roads are blocked by flood
blocked_roads_path, flood_polygon_path, stats = analyze_flood_impact()
```

---

### Tool #4: Safe Route Planner 🚗

**What It Does:**
This tool finds the shortest safe route between two places while avoiding blocked roads!

**Simple Explanation:**
Imagine you want to walk from your house to your school, but some streets are closed. This tool figures out the best way to go without using the closed streets!

**The Details:**

- **Finds:** Shortest path between two coordinates
- **Avoids:** Blocked roads (automatically removes them from the network)
- **Uses:** NetworkX algorithms (super smart computer math)
- **Returns:** A step-by-step route with every turn and street

**How It Works:**

1. Load the entire road network
2. Remove blocked roads from the network
3. Find the starting intersection (nearest to your start coordinate)
4. Find the ending intersection (nearest to your end coordinate)
5. Calculate the shortest route between them
6. Return the route as a series of coordinates

**Default Route:**

- **Start:** Colombo Fort (6.9271°, 80.7789°)
- **End:** Mount Lavinia (6.8520°, 80.8197°)

**What It Saves:**

- `optimal_route_colombo.geojson` - The planned route with every segment

**Python File:** `routing.py`

**Code Example:**

```python
from gis_tools.routing import plan_safe_route

# Plan a safe route avoiding blocked roads
route_path, route_gdf = plan_safe_route(
    start_coords=(6.9271, 80.7789),
    end_coords=(6.8520, 80.8197)
)
```

---

### Tool #5: GeoJSON Export Utility 💾

**What It Does:**
This tool saves all our map data in the GeoJSON format so that other programs can use it!

**Simple Explanation:**
All our tools create data on the computer's memory. This tool is like a photographer who takes all that information and saves it as files so you can look at it later, or other programs can use it!

**The Details:**

- **Validates:** Makes sure data is correct before saving
- **Converts:** Changes coordinate systems if needed
- **Organizes:** Saves data in the proper format
- **Documents:** Keeps track of what was saved

**Special Features:**

- Automatically creates folders if they don't exist
- Fixes broken data
- Checks coordinate systems (very important for maps!)
- Can save many files at once

**What It Does:**

- Ensures the CRS (Coordinate Reference System) is correct
- Validates that all shapes are valid
- Creates output directories automatically
- Saves with detailed metadata

**Python File:** `export_geojson.py`

**Code Example:**

```python
from gis_tools.export_geojson import save_geojson, save_geojson_batch

# Save a single GeoDataFrame
save_geojson(roads_gdf, "data/processed/roads.geojson")

# Save multiple files at once
save_geojson_batch({
    "roads": roads_gdf,
    "blocked_roads": blocked_gdf,
    "flood_zone": flood_gdf,
}, output_dir="data/processed/")
```

---

## How Everything Works Together 🔄

### The Complete Workflow

Here's how everything comes together like a beautiful machine:

#### Step 1: Get Satellite Images 📡

```
Real Space Satellite → Download Image → PNG File
```

The Sentinel-2 satellite takes a photo of Colombo and our tool downloads it.

#### Step 2: Get Road Information 🛣️

```
OpenStreetMap Database → Download Roads → Network Graph
```

Our tool asks for all the road information and stores it as a connected network.

#### Step 3: Analyze Flood Impact 💧

```
Satellite Image + Roads → Compare → Find Blocked Roads
```

Our tool compares where the water is (from satellite) with where the roads are to find which ones are blocked.

#### Step 4: Plan Safe Routes 🚗

```
Blocked Roads Removed + Network → Calculate Shortest Path → Safe Route
```

Our tool removes the blocked roads from the network and finds the fastest way to get from place A to place B.

#### Step 5: Save Everything 💾

```
All Data → Convert to GeoJSON → Save Files
```

Our tool saves all the information in a standard format that anyone can use.

### The Complete Picture

Imagine this scenario:

**Situation:** There's a big flood in Colombo! A rescue team needs to get from the Fire Station to a hospital.

**What Our System Does:**

1. **Downloads** a satellite image showing exactly where the water is
2. **Compares** the water location with all 20,000 roads in Colombo
3. **Identifies** that 237 roads are blocked by water
4. **Plans** the fastest safe route that avoids all 237 blocked roads
5. **Shows** the rescue team exactly which streets to drive on
6. **Saves** everything so other teams can use the same information

**Time Taken:** About 2-3 minutes!

**Time Without System:** 4-6 hours of manual checking!

---

## Using Our Tools 📚

### Before You Start

You need to set up a few things:

#### 1. Install Python

Python is a programming language. You need to install it on your computer. It's free!

#### 2. Set Up Your Environment File

Create a file called `.env` in your project folder:

```
SENTINEL_CLIENT_ID=your_client_id_here
SENTINEL_CLIENT_SECRET=your_client_secret_here
```

These are like passwords that let you download satellite images legally.

#### 3. Install All The Libraries

Libraries are like toolboxes that other people made. We use them to make our job easier!

Run this command in your terminal:

```bash
pip install -r requirements.txt
```

This installs everything we need!

### Requirements Explained

Our `requirements.txt` includes:

```
sentinelhub>=3.9.0          # For downloading satellite images
osmnx>=1.8.0                # For downloading road data
geopandas>=0.14.0           # For working with map data
shapely>=2.0.0              # For shapes (points, lines, polygons)
networkx>=3.1               # For finding routes
Pillow>=10.0.0              # For working with images
python-dotenv>=1.0.0        # For reading secret keys
numpy>=1.24.0               # For math
```

Each library does a specific job:

- **sentinelhub:** Talks to space satellites
- **osmnx:** Gets road information from OpenStreetMap
- **geopandas:** Works with geographical data
- **shapely:** Creates shapes on maps
- **networkx:** Finds the best paths/routes
- **Pillow:** Works with photos
- **python-dotenv:** Keeps secrets safe
- **numpy:** Does complicated math

### Using the Tools - Step by Step

#### Example 1: Download Satellite Images

```python
from gis_tools.download_sentinel2_rgb import download_sentinel2_rgb

# Download image
image = download_sentinel2_rgb()
print(f"Image saved to: {image}")
```

**What Happens:**

1. Tool connects to space satellite
2. Asks for a photo of Colombo
3. Downloads the photo
4. Saves it as a PNG file
5. Tells you where it saved it

#### Example 2: Download All Roads

```python
from gis_tools.road_network import download_and_process_road_network

# Download roads
edges, nodes, graph = download_and_process_road_network()
print(f"Roads saved to: {edges}")
```

**What Happens:**

1. Tool connects to OpenStreetMap
2. Asks for all roads in Colombo
3. Organizes them into a network
4. Saves the roads as GeoJSON files
5. Saves the network structure
6. Tells you where it saved everything

#### Example 3: Find Blocked Roads

```python
from gis_tools.flood_overlay import analyze_flood_impact

# Analyze flood impact
blocked_roads, flood_zone, stats = analyze_flood_impact()
print(f"Blocked roads: {stats['total_affected_roads']}")
print(f"Affected length: {stats['total_affected_length_m']} meters")
```

**What Happens:**

1. Tool loads the roads
2. Creates a flood zone (a circle of water)
3. Checks which roads cross through water
4. Marks them as blocked
5. Tells you how many roads and how much distance is affected

#### Example 4: Plan a Safe Route

```python
from gis_tools.routing import plan_safe_route

# Plan safe route
route, route_data = plan_safe_route(
    start_coords=(6.9271, 80.7789),  # Fort
    end_coords=(6.8520, 80.8197)     # Mount Lavinia
)
print(f"Route distance: {route_data['length_m'].sum()} meters")
```

**What Happens:**

1. Tool loads the entire road network
2. Removes blocked roads
3. Finds nearest roads to your starting point
4. Finds nearest roads to your ending point
5. Calculates the shortest safe path
6. Returns the route with every street name and turn

#### Example 5: Save Everything

```python
from gis_tools.export_geojson import save_geojson_batch

# Save multiple files
results = save_geojson_batch({
    "roads": roads_data,
    "blocked_roads": blocked_roads_data,
    "flood_zone": flood_data,
}, output_dir="data/processed/")
```

**What Happens:**

1. Tool checks that data is valid
2. Creates folders if needed
3. Converts data to proper format
4. Saves each file with correct structure
5. Tells you what was saved

---

## Understanding Coordinates 🌍

### What Are Coordinates?

Coordinates are like an address for every spot on Earth. Instead of saying "123 Main Street," we use two numbers:

**Latitude** - How far north or south you are
**Longitude** - How far east or west you are

### Format

Coordinates are written as: **[Longitude, Latitude]** or **(Latitude, Longitude)**

**Note:** Different systems use different orders! This is confusing, so be careful!

### Colombo Examples

Colombo has these important coordinates:

- **Colombo Fort:** (6.9271, 80.7789) - The old historical area
- **Mount Lavinia:** (6.8520, 80.8197) - A beach area to the south
- **Colombo City Center:** (6.9271, 80.7789) - The busy middle

### How Coordinates Work

Think of Earth like a big piece of graph paper:

```
         North Pole
             ↑
             |
West ← --- 0 --- → East
             |
             ↓
        South Pole
```

- **Latitude:** -90 to +90 (south to north)
- **Longitude:** -180 to +180 (west to east)

Colombo is:

- **Latitude 6.92°** = Very close to the equator, in the northern hemisphere
- **Longitude 80.78°** = In the eastern hemisphere, in Asia

---

## Understanding File Formats 📁

### GeoJSON Files

**File Extension:** `.geojson`

**What It Is:** A special JSON format for geographical data

**Example File Content:**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [80.7789, 6.9271],
          [80.78, 6.928]
        ]
      },
      "properties": {
        "name": "Galle Road",
        "blocked": false
      }
    }
  ]
}
```

**Can Open With:** Any text editor, mapping software, web browsers

### GraphML Files

**File Extension:** `.graphml`

**What It Is:** A format for storing network graphs

**Used For:** Storing the road network structure (which roads connect to which)

### PNG Files

**File Extension:** `.png`

**What It Is:** A picture format (like JPEG but better for maps)

**Used For:** Satellite images from space

---

## Common Questions & Answers ❓

### Q: Why do we use satellites?

**A:** Satellites can see areas that are hard to visit. They take photos from space and can see floods, damage, and other problems quickly. It's faster and safer than sending people to check!

### Q: What's OpenStreetMap?

**A:** It's like Wikipedia but for maps! It's a free database that anyone can help create and edit. It has maps of the whole world with roads, buildings, and other information.

### Q: Why can't we just use Google Maps?

**A:** We could, but OpenStreetMap is free for everyone to use, even for making our own tools. Google Maps has restrictions on how you can use it. For emergency situations, we need something freely available!

### Q: How accurate is this?

**A:** It depends! Satellite images can show large areas flooded, but might miss small details. Roads data from OpenStreetMap is usually pretty accurate but might have small outdated information. The combination gives us a good picture though!

### Q: Can this system work for other disasters?

**A:** Absolutely! Instead of floods, we could use the same tools to:

- Find blocked roads after earthquakes
- Plan routes around wildfires
- Navigate through snow storms
- Find accessible routes for people with disabilities
- Plan delivery routes in emergencies

### Q: How long does it take to run?

**A:**

- Downloading satellite images: 30-60 seconds
- Downloading roads: 2-5 minutes
- Analyzing impact: 1-2 minutes
- Planning routes: 10-30 seconds
- Total: About 5-10 minutes for everything!

### Q: Can we use this for real emergencies?

**A:** Yes! This is designed specifically for emergency response. Rescue teams, fire departments, and disaster management agencies can use these tools to make faster decisions during crises!

---

## Summary - The Big Picture 🎯

Our GIS project is an **amazing tool that helps save lives during disasters!**

**Here's what it does:**

1. **Gets satellite photos** from space showing where water/damage is
2. **Gets all the roads** from a map database
3. **Compares them** to find blocked roads
4. **Plans safe routes** for rescue teams
5. **Saves everything** so others can use it

**Why It's Important:**

During emergencies, **every second counts!** Our system can do in minutes what would take hours to do manually. This means:

- Rescue teams get help faster
- People can evacuate quicker
- More lives can be saved
- Resources are used more efficiently

**The Tools We Built:**

1. **Satellite Downloader** - Gets photos from space 📡
2. **Road Network Downloader** - Gets all the roads 🛣️
3. **Flood Impact Analyzer** - Finds blocked roads 💧
4. **Route Planner** - Plans safe paths 🚗
5. **GeoJSON Exporter** - Saves everything 💾

**All Together:**

These tools work like a team to solve a big problem. Each tool does one job really well, and together they create a system that helps during emergencies!

---

## Next Steps! 🚀

Now that you understand how everything works:

1. **Install the tools** - Set up Python and install the libraries
2. **Get API keys** - Sign up for Sentinel Hub to download satellite images
3. **Run the tools** - Try downloading images and roads
4. **Explore the data** - Look at the GeoJSON files in a map viewer
5. **Modify for your city** - Change the coordinates to analyze your own area!

---

## Final Thoughts 💭

This project shows how **technology can save lives!** By combining satellite images, map data, computer algorithms, and good organization, we created a system that can help during one of the scariest situations - natural disasters.

You can use these same tools to build even more amazing things:

- Emergency response systems
- Urban planning tools
- Environmental monitoring
- Disaster preparedness
- And so much more!

**Remember:** Every great technology starts with someone asking, "How can I help solve this problem?" That's exactly what we did here!

---

## Glossary - Big Words Explained 📚

| Word            | Simple Explanation                                                                |
| --------------- | --------------------------------------------------------------------------------- |
| **Algorithm**   | A set of steps to solve a problem (like a recipe but for computers)               |
| **Coordinates** | Two numbers that tell you exactly where something is on Earth                     |
| **CRS**         | A system that tells computer where coordinates are (EPSG:4326 is the most common) |
| **Database**    | A super organized collection of information                                       |
| **GIS**         | A computer system that works with maps and location data                          |
| **GeoJSON**     | A format for storing map data that computers can understand                       |
| **Graph**       | A network of connected points (like roads connected at intersections)             |
| **JSON**        | A standard way to write organized information                                     |
| **Library**     | Code that other people wrote to make our job easier                               |
| **Node**        | A point on a map (like an intersection)                                           |
| **Edge**        | A connection between points (like a road)                                         |
| **Polygon**     | A shape with a filled area (like a circle or rectangle)                           |
| **Overlay**     | Putting one map on top of another to compare them                                 |
| **Satellite**   | A machine in space that takes photos of Earth                                     |
| **Vector**      | Data stored as points, lines, and polygons (not photos)                           |

---

Thank you for reading this complete guide! Now you understand how our GIS system works, what GeoJSON and JSON are, and how technology can help save lives during emergencies. Pretty cool, right? 🌟
