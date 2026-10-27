# -*- coding: utf-8 -*-
"""US New Releases categories that hold large, mostly non-electric products."""
import re

BIG_CATS = re.compile(r"Furniture|Outdoor Storage|Cardio|Patio|Home Storage|Strollers|Tricycles|Air Mattresses|Pilates|"
                      r"Storage Racks|Sports Racks|Garage Storage|Pools, Hot Tubs|Baby Travel|Field, Court|Strength Training|"
                      r"Mirrors|Display Cases|Cycling|Outdoor Cooking|Stoves & Fireplaces|Outdoor Heating|Skates|Christmas Trees|"
                      r"Exercise|Fitness|Camping|Tents|Playground|Swing|Trampoline|Greenhouse|Shed|Kennel|Crates|Cat Furniture|"
                      r"Pet Beds|Grills|Gazebo|Canop|Hammock|Golf|Billiard|Table Tennis|Basketball|Workbench|Tool Storage|"
                      r"Ladders|Truck|Cargo|Bike|Kayak|Boating|Nursery|Kids' Furniture|Clothing & Closet", re.I)
