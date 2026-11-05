# -*- coding: utf-8 -*-
"""
1. generate ac area in the excel;
2. generate dc area in the excel;
3. generate ic location for ac and dc area;
4. form whole excel;
5. plot cases topology;
6. add variation for ac and dc system;
7. shrink the parameters space to achieve validation
8. save these cases
"""

from PowerflowAgent.ACDCPowerFlow import PowerCase
from PowerflowAgent.Visualization import PowerCaseResult
from GridCreate.GridGenerator import SynGrid
from typing import List, Tuple, Dict, Set, Optional, Union, Any
import re
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.gridspec as gridspec
# IEEE-style matplotlib fonts
plt.rcParams.update({
    'text.usetex': False,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'font.weight': 'normal',
    'font.size': 14,            # Base font size
    'axes.labelsize': 16,       # Axis label font size
    'axes.titlesize': 18,       # Title font size
    'xtick.labelsize': 14,      # Tick label font size
    'ytick.labelsize': 14,
    'legend.fontsize': 12,
    'figure.titlesize': 20,
    'lines.linewidth': 1.5,     # Line width
    'axes.linewidth': 1.2,      # Axis spine width
    'xtick.major.width': 1.2,
    'ytick.major.width': 1.2,
    'mathtext.fontset': 'stix', # Math text font
})
import math
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from concurrent.futures import ProcessPoolExecutor
import random
import itertools
import time
import copy
import networkx as nx
import numpy as np


class RegionType(Enum):
    AC = "AC"
    DC = "DC"


@dataclass
class ConverterType:
    """Structure for convereter information"""
    bus: int = None
    mode: int = None  # Converter mode
    C_bus: float = None  # C_bus
    Rg_pu: float = None  # Rg_pu
    Lg_pu: float = None  # Lg_pu
    f0: int = None


@dataclass
class RegionInfo:
    """Structure for region information"""
    index: int
    region_type: RegionType
    size: int
    name: str
    syngrid_instance: Any = None  # store the instance of SynGrid
    bus_offset: int = 0  # offset for bus size
    line_offset: int = 0  # offset for line size
    bus_map: Dict[int, int] = None  # mapping from local bus index to global bus index
    converter_locations: Set[int] = field(default_factory=set)  # given location for converters
    
    def __post_init__(self):
        # Ensure region index is a positive integer
        if self.index <= 0:
            raise ValueError(f"Region index must be a positive integer; got: {self.index}")
        # Ensure number of buses is a positive integer
        if self.size <= 0:
            raise ValueError(f"Region size (number of buses) must be a positive integer; got: {self.size}")
        if self.bus_map is None:
            self.bus_map = {}


@dataclass
class ConnectionInfo:
    """Structure for connection information"""
    from_region: int
    to_region: int
    converter_count: int = None  # number of converter
    converter_type: List = None  # show the explict type
    converter_list: List = None  # store the instance
    
    def __post_init__(self):
        # assure two regions are different
        if self.from_region == self.to_region:
            raise ValueError(f"A region cannot connect to itself: {self.from_region}")


def PROCESS_SINGLE_CASE(args):
    """a worker for Multiprocessing"""
    (i, combo, region_keys, self_regions,
     global_line_data, self_name, save_dir, other_data_dict) = args
    data_dict = dict()
    data_dict['Bus'] = list()
    data_dict['Network'] = list()
    # current_combo_info = dict(zip(i, combo, combo))
    # print(f"Processing case {i}: {current_combo_info}")  # optional progress

    # 3. Walk each region in the current combination and merge data
    for idx, region_key in enumerate(region_keys):
        variant_idx = combo[idx] # Selected variation index for this region
        region = self_regions[region_key]
        bus_map = region['bus_map']
        variant_idx += 1

        # Source data for this variation
        # Assumes data path is valid; read data_dict directly
        source_data = region['variations'][variant_idx][1].PF_system.data_dict
        # modify the area type
        std_data = region['std_data_bus']
        for bus_num, bus in enumerate(source_data['Bus']):
            bus['Area No.'] = std_data[bus_num]['Area No.']
            bus['ACorDCorIC'] = std_data[bus_num]['ACorDCorIC']
            bus['Type'] = std_data[bus_num]['Type']
        
        # --- Process Bus records ---
        local_bus_data = source_data.get('Bus', [])
        for bus_info in local_bus_data:
            local_bus_id = bus_info['Bus']
            # Map local bus ID to global ID via bus_map
            if int(local_bus_id) in bus_map:
                global_bus_id = bus_map[int(local_bus_id)]
                
                # Copy and update bus ID
                global_bus_info = copy.deepcopy(bus_info)
                global_bus_info['Bus'] = global_bus_id
                
                # Append to global list
                data_dict['Bus'].append(global_bus_info)
            else:
                print(f"Warning: region {region_key} bus ID {local_bus_id} not found in bus_map")

        # --- Process Network (line) data ---
        local_line_data = source_data.get('Network', [])
        for line_info in local_line_data:
            global_line_info = {}
            
            # Map From/To bus IDs
            try:
                # Source may use 'FromBus'; target style may use 'From bus' (with space)
                # Keep source key FromBus and target keys From bus / To bus
                from_bus_local = line_info['FromBus']
                to_bus_local = line_info['ToBus']
                
                global_line_info['From bus'] = bus_map[int(from_bus_local)]
                global_line_info['To bus'] = bus_map[int(to_bus_local)]
                
                # Copy remaining fields
                for key, value in line_info.items():
                    if key not in ['FromBus', 'ToBus']:
                        global_line_info[key] = value
                
                data_dict['Network'].append(global_line_info)
                
            except KeyError as e:
                 print(f"Warning: region {region_key} line record missing key or bus map failed: {e}")
    # --- Inter-area network branches ---
    for branch in global_line_data:
        branch_copy = copy.deepcopy(branch)
        branch_copy['From bus'] = branch_copy.pop('FromBus')
        branch_copy['To bus'] = branch_copy.pop('ToBus')
        data_dict['Network'].append(branch_copy)
    # optional extra sheets
    for key, value in other_data_dict.items():
        data_dict.setdefault(key, value)

    # 4. Save this combination to Excel
    filename = f"{self_name}_var_{i+1}.xlsx"        
    filepath = os.path.join(save_dir, filename)
    
    # Write Excel and validate
    try:
        std_excel = GridInit._store_excel(filename, filepath, data_dict)
        # validate
        start_time = time.time()  # time begin
        temp_object = PowerCase(f"{self_name}_var_{i+1}", std_excel, 'S')
        end_time = time.time()  # time begin
        single_time = end_time - start_time
        case_name = f"{self_name}_var_{i+1}"
        # print("")
        print(f"Validated OK: {filename}")
        return (case_name, single_time, temp_object.PF_system.solving_information)
        # print("")
    except Exception as e:
        print(f"Validation failed for {filename}: {e}")
        return 0


class ICPlacement(object):
    def __init__(self):
        # CONSTANTS for Location Generators
        # AC/DC score weights: [degree, electrical, neighborhood, penalty]
        self.w_score = [0.25, 0.35, 0.25, 0.15]  # AC/DC Score weights
        # Link score weights: [DC term, match term]
        self.w_link = [0.5, 0.5]            # Link Score weights
        self.mu = 5.0   # Sensitivity scale (mu)
        # --- Data storage layout ---
        # 1. Per region: graph and per-node scores
        # Shape: { region_id: {'graph': nx.Graph, 'scores': dict, 'components': dict, 'type': 'AC'/'DC'} }
        self.region_data = {} 
        
        # 2. Per AC-DC pair: link matrix and selection
        # Shape: { (ac_id, dc_id): {'matrix': dict, 'selected': list} }
        self.connection_data = {}
        

    def _build_graph(self, bus_data, network_data):
        """Build networkx graph helper."""
        G = nx.Graph()
        for bus in bus_data:
            G.add_node(int(bus['Bus']))
        for line in network_data:
            f, t = int(line['FromBus']), int(line['ToBus'])
            r, x = line.get('R (pu)', 0), line.get('X (pu)', 0)
            z_mag = math.sqrt(r**2 + x**2)
            weight = z_mag if z_mag > 1e-6 else 1e-6
            G.add_edge(f, t, weight=weight)
        return G


    def _calc_single_region_scores(self, G, used_buses):
            """Compute per-node scores for a region."""
            nodes = list(G.nodes())
            if not nodes: return {}, {}
    
            degrees = dict(G.degree())
            max_deg = max(degrees.values()) if degrees else 1
            
            z_avgs = {}
            for n in nodes:
                try:
                    dists = nx.shortest_path_length(G, source=n, weight='weight')
                    avg_dist = np.mean(list(dists.values()))
                    z_avgs[n] = avg_dist
                except nx.NetworkXNoPath:
                    z_avgs[n] = float('inf')
            
            valid_z = [z for z in z_avgs.values() if z > 0 and z != float('inf')]
            min_z = min(valid_z) if valid_z else 1.0
    
            scores = {}
            components = {}
            
            for n in nodes:
                if n in used_buses:
                    scores[n] = -1.0 # Mark as unavailable
                    continue
    
                t1 = degrees[n] / max_deg
                t2 = (min_z / z_avgs[n]) if z_avgs[n] > 0 and z_avgs[n] != float('inf') else 0
                
                nbs = list(G.neighbors(n))
                t3 = sum(degrees[k] for k in nbs) / (degrees[n] * max_deg) if degrees[n] > 0 else 0
                
                penalty = 0
                valid_p_count = 0
                for existing in used_buses:
                    try:
                        d = nx.shortest_path_length(G, source=n, target=existing, weight='weight')
                        if d > 1e-4: penalty += 1.0 / d
                        else: penalty += 10.0
                        valid_p_count += 1
                    except: pass
                
                # Sigmoid-style normalization for penalty term
                avg_p = penalty / max(valid_p_count, 1) if valid_p_count > 0 else 0
                t4 = 1.0 / (1.0 + math.exp(-avg_p)) - 0.5 
    
                total = (self.w_score[0]*t1 + self.w_score[1]*t2 + 
                         self.w_score[2]*t3 - self.w_score[3]*t4)
                scores[n] = total
                components[n] = {'degree': t1, 'elec': t2, 'neb': t3, 'pen': t4}
    
            return scores, components
            

    def select_best_pairs(self, ac_id, ac_data, dc_id, dc_data, ac_used, dc_used, count):
        """
        Key change: ac_id and dc_id distinguish different regions.
        """
        # 1. Build/update AC region graph and scores
        # Recompute if the used-bus set changes even if the graph is unchanged
        G_ac = self._build_graph(ac_data['Bus'], ac_data['Network'])
        s_ac, comp_ac = self._calc_single_region_scores(G_ac, ac_used)
        
        # Store in region_data
        self.region_data[ac_id] = {
            'graph': G_ac, 'scores': s_ac, 'components': comp_ac, 'type': 'AC'
        }

        # 2. Build/update DC region graph and scores
        G_dc = self._build_graph(dc_data['Bus'], dc_data['Network'])
        s_dc, comp_dc = self._calc_single_region_scores(G_dc, dc_used)
        
        self.region_data[dc_id] = {
            'graph': G_dc, 'scores': s_dc, 'components': comp_dc, 'type': 'DC'
        }

        # 3. Pairwise link scores (Cartesian product)
        valid_ac = {k: v for k, v in s_ac.items() if v != -1.0}
        valid_dc = {k: v for k, v in s_dc.items() if v != -1.0}

        link_matrix = {}
        candidates = []

        for u, val_ac in valid_ac.items():
            link_matrix[u] = {} # [Fix] initialize row dict to avoid KeyError
            for v, val_dc in valid_dc.items():
                comp = math.exp(-self.mu * abs(val_ac - val_dc))
                s_link = self.w_link[0]*val_dc + self.w_link[1]*comp
                
                link_matrix[u][v] = s_link
                candidates.append({'ac': u, 'dc': v, 'score': s_link})

        # 4. Sort and select top pairs
        candidates.sort(key=lambda x: x['score'], reverse=True)
        results = []
        temp_ac, temp_dc = set(), set()
        
        for cand in candidates:
            if len(results) >= count: break
            if cand['ac'] not in temp_ac and cand['dc'] not in temp_dc:
                results.append((cand['ac'], cand['dc']))
                temp_ac.add(cand['ac'])
                temp_dc.add(cand['dc'])
        
        # Fill remaining slots if needed
        while len(results) < count:
             rem_ac = [k for k in valid_ac if k not in temp_ac]
             rem_dc = [k for k in valid_dc if k not in temp_dc]
             if not rem_ac or not rem_dc: break
             u, v = random.choice(rem_ac), random.choice(rem_dc)
             results.append((u, v))
             temp_ac.add(u)
             temp_dc.add(v)

        # 5. Store connection data
        self.connection_data[(ac_id, dc_id)] = {
            'matrix': link_matrix,
            'selected': results
        }

        return results
    
    
    def select_random_pairs(self, ac_data, dc_data, ac_used, dc_used, count):
        results = list()
        round_used_ac = set()
        round_used_dc = set()
        for num in range(count):
            ac_local = ICPlacement._generate_ic_ac_loc(ac_data, ac_used, round_used_ac)
            dc_local = ICPlacement._generate_ic_dc_loc(dc_data, dc_used, round_used_dc)
            round_used_ac.add(ac_local)
            round_used_dc.add(dc_local)
            results.append((ac_local, dc_local))
        print(results)
        return results

    
    @staticmethod
    def _generate_ic_ac_loc(ac_data, total_used_ac, round_used_ac):
        """generate ic location in ac side"""        
        # Count AC buses
        bus_data = ac_data['Bus']
        # network_data = ac_area_instance.std_powercase.PF_system.data_dict['Network']
        bus_count = len(bus_data)
        # Random bus among not yet used
        used_bus = total_used_ac | round_used_ac
        available_buses = [bus_id for bus_id in range(1, bus_count + 1) 
                          if bus_id not in used_bus]
        
        if available_buses:
            # If any bus remains, pick one
            chosen_bus = random.choice(available_buses)
        return chosen_bus


    @staticmethod
    def _generate_ic_dc_loc(dc_data, total_used_dc, round_used_dc):
        """generate ic location in dc side"""
        # Count DC buses
        bus_data = dc_data['Bus']
        bus_count = len(bus_data)
        
        # Random bus among not yet used 
        used_bus = total_used_dc | round_used_dc
        available_buses = [bus_id for bus_id in range(1, bus_count + 1) 
                          if bus_id not in used_bus]
        
        if available_buses:
            # If any bus remains, pick one
            chosen_bus = random.choice(available_buses)
        return chosen_bus


    def plot_region_scores(self, region_ids='all', save_path=None):
        """
        Plot node score distribution for selected regions.
        :param region_ids: 'all' or list of region IDs, e.g. [1, 2]
        """
        target_ids = list(self.region_data.keys()) if region_ids == 'all' else region_ids
        
        for rid in target_ids:
            if rid not in self.region_data:
                print(f"Region {rid} not found in data.")
                continue
            
            data = self.region_data[rid]
            # Filename suffix
            suffix = f"region_{rid}"
            file_name = f"{suffix}.png"
            path = os.path.join(save_path, file_name) if save_path else None
            title = f"{data['type']} Area {rid} - Suitability Scores"
            
            self._plot_single_region_figure(
                data['graph'], data['scores'], title, path
            )

    def _plot_single_region_figure(self, G, scores, title, save_path):
        """Plot one region: topology + histogram."""
        valid_nodes = [n for n in G.nodes() if scores.get(n, -1) != -1.0]
        if not valid_nodes: return

        # Large figure for readable fonts when scaled
        fig = plt.figure(figsize=(14, 6), dpi=300) 
        gs = gridspec.GridSpec(1, 2, width_ratios=[1.6, 1], wspace=0.15)

        # --- Left: topology ---
        ax1 = plt.subplot(gs[0])
        pos = nx.spring_layout(G, seed=42, k=0.3/math.sqrt(len(G.nodes())))
        
        valid_scores = [scores[n] for n in valid_nodes]
        vmin, vmax = min(valid_scores), max(valid_scores)
        
        # Background edges and invalid nodes
        nx.draw_networkx_edges(G, pos, ax=ax1, edge_color='#B0B0B0', alpha=0.4, width=1.0)
        invalid_nodes = [n for n in G.nodes() if n not in valid_nodes]
        nx.draw_networkx_nodes(G, pos, nodelist=invalid_nodes, ax=ax1, 
                               node_size=80, node_color='#E0E0E0', alpha=0.5)
        
        # Valid nodes (Viridis colormap)
        nodes = nx.draw_networkx_nodes(G, pos, nodelist=valid_nodes, ax=ax1,
                                       node_size=350, node_color=valid_scores,
                                       cmap='viridis', alpha=0.95, 
                                       edgecolors='black', linewidths=0.8)
        
        # Node labels if graph is small
        if len(G.nodes()) < 80:
            nx.draw_networkx_labels(G, pos, ax=ax1, font_size=10, 
                                    font_family='serif', font_weight='bold')
        
        # ax1.set_title("Topology & Score Distribution", fontweight='bold', pad=10)
        ax1.axis('off')
        
        # Colorbar placement
        cbar = plt.colorbar(nodes, ax=ax1, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(labelsize=12)
        # cbar.set_label('Suitability Score', fontsize=14)

        # --- Right: histogram ---
        ax2 = plt.subplot(gs[1])
        # IEEE-style blue bars
        ax2.hist(valid_scores, bins=15, color='#2E5A88', 
                 edgecolor='black', linewidth=1.0, alpha=0.85)
        
        # ax2.set_xlabel('Score')
        # ax2.set_ylabel('Frequency')
        # ax2.set_title('Score Histogram', fontweight='bold', pad=10)
        
        # Axis styling
        ax2.grid(True, linestyle=':', alpha=0.6, color='gray')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_linewidth(1.2)
        ax2.spines['bottom'].set_linewidth(1.2)

        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            # print(f"[Plot] Saved: {save_path}")
        plt.show()

    def plot_connection_heatmaps(self, save_path=None):
        """
        Plot heatmaps for all processed AC-DC link matrices.
        """
        if not self.connection_data:
            print("No connection data found.")
            return

        for (ac_id, dc_id), data in self.connection_data.items():
            matrix_dict = data['matrix']
            selected = data['selected']
            
            # Build matrix
            ac_nodes = sorted(matrix_dict.keys())
            if not ac_nodes: continue
            dc_nodes = sorted(matrix_dict[ac_nodes[0]].keys())
            
            matrix = np.zeros((len(ac_nodes), len(dc_nodes)))
            for i, u in enumerate(ac_nodes):
                for j, v in enumerate(dc_nodes):
                    matrix[i, j] = matrix_dict[u].get(v, 0)

            # Plot
            fig, ax = plt.subplots(figsize=(8, 7), dpi=300) # Square layout suits heatmaps
            
            # coolwarm emphasizes high vs low scores
            im = ax.imshow(matrix, cmap='coolwarm', aspect='auto', interpolation='nearest')
            
            # Axis ticks
            step_ac = max(1, len(ac_nodes) // 15)
            step_dc = max(1, len(dc_nodes) // 15)
            
            ax.set_yticks(np.arange(0, len(ac_nodes), step_ac))
            ax.set_yticklabels([ac_nodes[i] for i in range(0, len(ac_nodes), step_ac)])
            ax.set_xticks(np.arange(0, len(dc_nodes), step_dc))
            ax.set_xticklabels([dc_nodes[i] for i in range(0, len(dc_nodes), step_dc)], rotation=45)
            
            ax.set_xlabel(f'DC Area {dc_id} Nodes')
            ax.set_ylabel(f'AC Area {ac_id} Nodes')
            ax.set_title(f'Link Suitability: Area {ac_id} vs {dc_id}', fontweight='bold', pad=15)
            
            # Colorbar
            cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label('Link Score', fontsize=14)
            
            # Mark selected pairs for print visibility
            for (u, v) in selected:
                if u in ac_nodes and v in dc_nodes:
                    i = ac_nodes.index(u)
                    j = dc_nodes.index(v)
                    ax.plot(j, i, 'o', markerfacecolor='none', markeredgecolor='black', 
                            markersize=12, markeredgewidth=2.0)
                    ax.plot(j, i, 'x', color='black', markersize=8, markeredgewidth=2.0)

            plt.tight_layout()
            
            if save_path:
                file_name = f"link_{ac_id}_{dc_id}.png"
                fname = os.path.join(save_path, file_name) if save_path else None
                plt.savefig(fname, bbox_inches='tight', dpi=300)
                # print(f"[Plot] Saved: {fname}")
            plt.show()


class GridInit(object):
    # four types of control modes
    MODES = {"PQ": 0, "EQ": 1, "PU": 2, "EU": 3}
    P_MODES = ["PQ", "PU"]  # which contains P modes
    E_MODES = ["EQ", "EU"]  # which contains E modes
    # 3 is Slack, 2 is PV, 1 is PQ
    MODES_TYPE = {0: [1,1], 1: [1,3], 2:[2,1], 3:[2,3]}
    def __init__(self, name, area_index_size_list, index_with_index_list=list()):
        """
        Initialization for the generated network:
        Args:
            name: Case name
            area_index_size_list: Region specs like ['AC_1_50', 'DC_2_30', 'AC_3_40']
                                Pattern: TYPE_INDEX_NUMBUSES
            index_with_index_list: Links like ['1_with_2', '2_with_3']
                                Pattern: idx_with_idx
        Examples:
            >>> grid = GridInit("TestGrid", ['AC_1_50', 'DC_2_30'], ['1_with_2'])
        """
        
        self.name = name
        self.area_index_size_list = area_index_size_list
        self.index_with_index_list = index_with_index_list
        
        self.global_line_data= list()
        self.data_dict = dict()
        self.ic_postion = None
        self.multi_variation_information = dict()
        
        self._validate_input_format()
        # area information
        self.regions = self._parse_regions()  # Dict[int, RegionInfo]
        # connection information
        self.connections = self._parse_connections()  # List[ConnectionInfo]
        # further validation
        self._validate_connections()

    
    def _validate_input_format(self) -> None:
        """Validate constructor string formats."""
        errors = []
        
        # Validate region list
        if not self.area_index_size_list:
            errors.append("area_index_size_list must not be empty")
        
        # Validate region string format
        for i, area_str in enumerate(self.area_index_size_list):
            if not isinstance(area_str, str):
                errors.append(f"Each region spec must be a string; index {i}: {area_str}")
                continue
                
            parts = area_str.split('_')
            if len(parts) < 3:
                errors.append(f"Invalid region spec '{area_str}'; expected 'TYPE_INDEX_SIZE'")
                continue
            
            # Validate region type
            region_type = parts[0].upper()
            if region_type not in ['AC', 'DC']:
                errors.append(f"Invalid region type in '{area_str}'; allowed: AC or DC")
            
            # Validate region index
            try:
                index = int(parts[1])
                if index <= 0:
                    errors.append(f"Region index must be a positive integer: '{area_str}'")
            except ValueError:
                errors.append(f"Region index must be numeric: '{area_str}'")
            
            # Validate bus count
            try:
                size = int(parts[2])
                if size <= 0:
                    errors.append(f"Region bus count must be a positive integer: '{area_str}'")
            except ValueError:
                errors.append(f"Region bus count must be numeric: '{area_str}'")
        
        # Validate link format
        for i, conn_str in enumerate(self.index_with_index_list):
            if not isinstance(conn_str, str):
                errors.append(f"Each link spec must be a string; index {i}: {conn_str}")
                continue
            
            if '_with_' not in conn_str:
                errors.append(f"Invalid link spec '{conn_str}'; expected 'idx_with_idx'")
                continue
            
            parts = conn_str.split('_with_')
            if len(parts) != 2:
                errors.append(f"Invalid link spec '{conn_str}'; expected 'idx_with_idx'")
                continue
            
            try:
                from_idx = int(parts[0])
                to_idx = int(parts[1])
                
                if from_idx <= 0 or to_idx <= 0:
                    errors.append(f"Link indices must be positive integers: '{conn_str}'")
            except ValueError:
                errors.append(f"Link indices must be numeric: '{conn_str}'")
        
        if errors:
            error_msg = "Invalid input:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)


    def _parse_regions(self) -> Dict[int, RegionInfo]:
        """Parse region specifications."""
        regions = {}
        seen_indices: Set[int] = set()
        seen_names: Set[str] = set()
        
        for area_str in self.area_index_size_list:
            parts = area_str.split('_')
            
            region_type = RegionType(parts[0].upper())
            index = int(parts[1])
            size = int(parts[2])
            
            # Region label
            name = f"{region_type.value}_{index}"
            
            # Duplicate index check
            if index in seen_indices:
                raise ValueError(f"Duplicate region index: {index}")
            seen_indices.add(index)
            
            # Duplicate name guard
            if name in seen_names:
                raise ValueError(f"Duplicate region name: {name}")
            seen_names.add(name)
            
            # Build RegionInfo
            regions[index] = RegionInfo(
                index=index,
                region_type=region_type,
                size=size,
                name=name
            )
        
        return regions


    def _parse_connections(self) -> List[ConnectionInfo]:
        """Parse inter-region links."""
        connections = []
        
        for conn_str in self.index_with_index_list:
            parts = conn_str.split('_with_')
            from_idx = int(parts[0])
            to_idx = int(parts[1])
            
            # Ensure endpoints exist
            if from_idx not in self.regions:
                raise ValueError(f"Region index in link not found: {from_idx}")
            if to_idx not in self.regions:
                raise ValueError(f"Region index in link not found: {to_idx}")
            
            from_region = self.regions[from_idx]
            to_region = self.regions[to_idx]
            
            if from_region.region_type != to_region.region_type:
                # random converter count
                converter_count = random.randint(2, 5)  # between 2 and 5 
                # randomly with P
                p_choice = random.choice(GridInit.P_MODES)
                # randomly with E
                e_choices = [mode for mode in GridInit.E_MODES if mode != p_choice]
                if e_choices:
                    e_choice = random.choice(e_choices)
                else:
                    e_choice = random.choice(GridInit.E_MODES)
                # Start with one P-mode and one E-mode converter
                converter_type = [p_choice, e_choice]
                # Add extra converters if count > 2
                if converter_count > 2:
                    # Remaining slots = converter_count - 2
                    for _ in range(converter_count - 2):
                        # Sample remaining modes (duplicates allowed)
                        converter_type.append(random.choice(list(GridInit.MODES.keys())))
                # Shuffle so P/E are not forced to the front
                random.shuffle(converter_type)
            else:
                raise ValueError(f"Cannot link two regions of the same type: {from_region.region_type}_{to_region.region_type}")
            
            converter_list = list()
            for converter in converter_type:
                # the parameters will be given later
                converter_instance = ConverterType(mode=GridInit.MODES[f'{converter}'])
                converter_list.append(converter_instance)
                
            # Normalize ordering so from_region < to_region
            if from_idx < to_idx:
                conn = ConnectionInfo(from_region=from_idx, to_region=to_idx,
                                      converter_count = converter_count,
                                      converter_type = converter_type,
                                      converter_list = converter_list)
            else:
                conn = ConnectionInfo(from_region=to_idx, to_region=from_idx,
                                      converter_count = converter_count,
                                      converter_type = converter_type,
                                      converter_list = converter_list)
            
            # Duplicate link guard
            existing_conn = (conn.from_region, conn.to_region)
            for existing in connections:
                if (existing.from_region, existing.to_region) == existing_conn:
                    raise ValueError(f"Duplicate connection: {from_idx} and {to_idx}")
            
            connections.append(conn)
        
        return connections


    def _validate_connections(self) -> None:
        """Validate connectivity (no isolated regions)."""
        # Detect isolated regions
        connected_regions: Set[int] = set()
        for conn in self.connections:
            connected_regions.add(conn.from_region)
            connected_regions.add(conn.to_region)
        
        all_regions = set(self.regions.keys())
        isolated_regions = all_regions - connected_regions
        
        if len(self.regions) > 1 and isolated_regions:
            isolated_str = ", ".join(str(idx) for idx in sorted(isolated_regions))
            print(f"Warning: isolated regions (no inter-area link): {isolated_str}")
    
    
    def _generate_ac_area(self, region: RegionInfo, bus_offset: int, line_offset: int):
        """Single AC region"""
        # SynGrid for single AC region
        region_name = f"{self.name}_{region.name}"
        syn_grid = SynGrid(region_name, region.size, 'AC', self.name)
        syn_grid.generate_mpc()
        for bus in syn_grid.std_powercase.PF_system.data_dict['Bus']:
            bus['Area No.'] = region.index
            bus['ACorDCorIC'] = 'AC'
        # store the instance of SynGrid
        region.syngrid_instance = syn_grid
        # store the offset
        region.bus_offset = bus_offset
        region.line_offset = line_offset
        # create the index mapping
        local_bus_data = syn_grid.std_powercase.PF_system.data_dict['Bus']
        for local_bus in local_bus_data:
            local_bus_id = local_bus['Bus']
            global_bus_id = bus_offset + int(local_bus_id)
            region.bus_map[int(local_bus_id)] = global_bus_id
        # print(f"  Region {region.index} built; buses {bus_offset+1} .. {bus_offset+region.size}")


    def _generate_dc_area(self, region: RegionInfo, bus_offset: int, line_offset: int):
        """Single DC region"""
        # SynGrid for single DC region
        region_name = f"{self.name}_{region.name}"
        syn_grid = SynGrid(region_name, region.size, 'DC', self.name)
        syn_grid.generate_mpc()
        for bus in syn_grid.std_powercase.PF_system.data_dict['Bus']:
            bus['Area No.'] = region.index
            bus['ACorDCorIC'] = 'DC'
            if bus['Type'] == 2:
                bus['Type'] = random.choice([1, 3])
        # store the instance of SynGrid
        region.syngrid_instance = syn_grid
        # store the offset
        region.bus_offset = bus_offset
        region.line_offset = line_offset
        # create the index mapping
        local_bus_data = syn_grid.std_powercase.PF_system.data_dict['Bus']
        for local_bus in local_bus_data:
            local_bus_id = local_bus['Bus']
            global_bus_id = bus_offset + int(local_bus_id)
            region.bus_map[int(local_bus_id)] = global_bus_id
        # print(f"  Region {region.index} (DC) built; buses {bus_offset+1} .. {bus_offset+region.size}")
    
    
    def _generate_std_excel(self):
        """generate the whole excel in the chosen file root"""
        self.data_dict = {
            'Bus': [],      # bus records
            'Network': [],  # branch records
            'IC': []
        }
        # write region
        for region in self.regions.values():
            region_dict = region.syngrid_instance.std_powercase.PF_system.data_dict
            local_bus_data = region_dict['Bus']
            local_line_data  = region_dict['Network']
            # Merge bus tables
            for bus_info in local_bus_data:
                local_bus_id = bus_info['Bus']
                global_bus_id = region.bus_map[int(local_bus_id)]
                # Clone bus row and rewrite global ID
                global_bus_info = copy.deepcopy(bus_info)
                global_bus_info['Bus'] = global_bus_id
                self.data_dict['Bus'].append(global_bus_info)
            # merge branch records
            for line_info in local_line_data:
                global_line_info = {}
                # keep the order of from bus and to bus
                # 1. From bus
                global_line_info['From bus'] = region.bus_map[line_info['FromBus']]
                # 2. To bus
                global_line_info['To bus'] = region.bus_map[line_info['ToBus']]
                # 3. Remaining keys
                for key, value in line_info.items():
                    if key not in ['FromBus', 'ToBus']:
                        global_line_info[key] = value
                self.data_dict['Network'].append(global_line_info)
        # append inter-area branches
        for branch in self.global_line_data:
            branch_copy = copy.deepcopy(branch)
            branch_copy['From bus'] = branch_copy.pop('FromBus')
            branch_copy['To bus'] = branch_copy.pop('ToBus')
            self.data_dict['Network'].append(branch_copy)
        # append IC rows
        for area in self.connections:
            for ic in area.converter_list:
                self.data_dict['IC'].append(asdict(ic))
        # optional extra sheets
        for key, value in region_dict.items():
            self.data_dict.setdefault(key, value)
            
        # export formatted workbook
        filename = f"{self.name}.xlsx"
        filepath = f"./CasesResult/GridCreateProject_{self.name}/{filename}"
        return GridInit._store_excel(filename, filepath, self.data_dict)


    @staticmethod
    def _store_excel(filename, filepath, data_dict):
        """store excel with format"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, data in data_dict.items():
                safe_sheet_name = str(sheet_name)[:31]
                # Handle Basic sheet
                if sheet_name == 'Basic':
                    if isinstance(data, dict):                        
                        # Single-row DataFrame
                        df = pd.DataFrame([data])
                        df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                        # print(f"  ✓ {sheet_name}")
                    continue
                # Other sheets
                if isinstance(data, dict) and data:
                    df = pd.DataFrame.from_dict(data, orient='index')
                    df.to_excel(writer, sheet_name=safe_sheet_name, index=True, index_label=f'{sheet_name}_ID')
                elif isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                else:
                    # Empty sheet placeholder
                    pd.DataFrame().to_excel(writer, sheet_name=safe_sheet_name, index=False)
                
                # print(f"  ✓ {sheet_name}")
        
            # Format workbook
            # Active workbook
            workbook = writer.book
            # Styles
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True, size=11)
            center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            # Apply styles per sheet
            for sheet_name in data_dict.keys():
                safe_sheet_name = str(sheet_name)[:31]
                if safe_sheet_name in workbook.sheetnames:
                    worksheet = workbook[safe_sheet_name]
                    # Center all cells
                    for row in worksheet.iter_rows():
                        for cell in row:
                            cell.alignment = center_alignment
                            cell.border = thin_border
                    # Header row style
                    for cell in worksheet[1]:
                        cell.fill = header_fill
                        cell.font = header_font
                    # Auto column width
                    for column in worksheet.columns:
                        column_letter = get_column_letter(column[0].column)
                        max_length = 0
                        for cell in column:
                            try:
                                if cell.value:
                                    # Measure cell text width
                                    cell_value = str(cell.value)
                                    if '\n' in cell_value:
                                        # Multi-line: max line length
                                        lines = cell_value.split('\n')
                                        cell_length = max(len(line) for line in lines)
                                    else:
                                        cell_length = len(cell_value)
                                    
                                    # Wider cells for CJK if present in cell text
                                    cjk_chars = sum(1 for c in cell_value if '\u4e00' <= c <= '\u9fff')
                                    cell_length += cjk_chars * 0.5  # extra width for CJK
                                    
                                    if cell_length > max_length:
                                        max_length = cell_length
                            except:
                                pass
                        # Clamp column width
                        adjusted_width = min(max(max_length + 2, 8), 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                    # Row height for wrapped cells
                    for row in worksheet.iter_rows():
                        for cell in row:
                            if cell.value and '\n' in str(cell.value):
                                # Extra height when newline present
                                line_count = str(cell.value).count('\n') + 1
                                worksheet.row_dimensions[cell.row].height = 15 * line_count
                    # Freeze header row
                    worksheet.freeze_panes = 'A2'
                    # Alternating row shading
                    GridInit._apply_alternating_row_colors(worksheet)
                    # print(f"    {sheet_name}: formatting done")
        
        # print(f"\nExcel written: {filepath}")
        return filename


    def _std_excels(self):
        """Enumerate variations sequentially (single process)."""
        # 1. Variation counts per region
        return_list = list()
        region_variant_counts = {}
        region_keys = list(self.regions.keys())
        variant_ranges = []
        
        for region_key in region_keys:
            region = self.regions[region_key]
            variant_count = len(region.syngrid_instance.variation_case)
            region_variant_counts[region_key] = variant_count
            variant_ranges.append(range(variant_count))
        
        # print(f"Variations per region: {region_variant_counts}")
        
        # 2. Iterate each Cartesian product
        # enumerate yields case index i (0, 1, 2, ...)
        for i, combo in enumerate(itertools.product(*variant_ranges)):
            self.data_dict['Bus'] = list()
            self.data_dict['Network'] = list()
            # current_combo_info = dict(zip(region_keys, combo))
            # print(f"Processing case {i}: {current_combo_info}")  # optional progress
        
            # 3. Walk each region in the current combination and merge data
            for idx, region_key in enumerate(region_keys):
                variant_idx = combo[idx] # Selected variation index for this region
                region = self.regions[region_key]
                variant_idx += 1

                # Source data for this variation
                # Assumes data path is valid; read data_dict directly
                source_data = region.syngrid_instance.variation_case[variant_idx][1].PF_system.data_dict
                # modify the area type
                std_data = region.syngrid_instance.std_powercase.PF_system.data_dict['Bus']
                for bus_num, bus in enumerate(source_data['Bus']):
                    bus['Area No.'] = std_data[bus_num]['Area No.']
                    bus['ACorDCorIC'] = std_data[bus_num]['ACorDCorIC']
                    bus['Type'] = std_data[bus_num]['Type']
                
                # --- Process Bus records ---
                local_bus_data = source_data.get('Bus', [])
                for bus_info in local_bus_data:
                    local_bus_id = bus_info['Bus']
                    # Map local bus ID to global ID via bus_map
                    if int(local_bus_id) in region.bus_map:
                        global_bus_id = region.bus_map[int(local_bus_id)]
                        
                        # Copy and update bus ID
                        global_bus_info = copy.deepcopy(bus_info)
                        global_bus_info['Bus'] = global_bus_id
                        
                        # Append to global list
                        self.data_dict['Bus'].append(global_bus_info)
                    else:
                        print(f"Warning: region {region_key} bus ID {local_bus_id} not found in bus_map")
        
                # --- Process Network (line) data ---
                local_line_data = source_data.get('Network', [])
                for line_info in local_line_data:
                    global_line_info = {}
                    
                    # Map From/To bus IDs
                    try:
                        # Source may use 'FromBus'; target style may use 'From bus' (with space)
                        # Keep source key FromBus and target keys From bus / To bus
                        from_bus_local = line_info['FromBus']
                        to_bus_local = line_info['ToBus']
                        
                        global_line_info['From bus'] = region.bus_map[int(from_bus_local)]
                        global_line_info['To bus'] = region.bus_map[int(to_bus_local)]
                        
                        # Copy remaining fields
                        for key, value in line_info.items():
                            if key not in ['FromBus', 'ToBus']:
                                global_line_info[key] = value
                        
                        self.data_dict['Network'].append(global_line_info)
                        
                    except KeyError as e:
                         print(f"Warning: region {region_key} line record missing key or bus map failed: {e}")
            # --- Inter-area network branches ---
            for branch in self.global_line_data:
                branch_copy = copy.deepcopy(branch)
                branch_copy['From bus'] = branch_copy.pop('FromBus')
                branch_copy['To bus'] = branch_copy.pop('ToBus')
                self.data_dict['Network'].append(branch_copy)
        
            # 4. Save this combination to Excel
            filename = f"{self.name}_var_{i+1}.xlsx"
            # Ensure output directory
            save_dir = f"./CasesResult/GridCreateProject_{self.name}/variation/"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                
            filepath = os.path.join(save_dir, filename)
            
            # Write Excel and validate
            try:
                std_excel = GridInit._store_excel(filename, filepath, self.data_dict)
                # validate
                start_time = time.time()
                temp_object = PowerCase(f"{self.name}_var_{i+1}", std_excel, 'S')
                end_time = time.time()  # time begin
                single_time = end_time - start_time
                case_name = f"{self.name}_var_{i+1}"
                # print("")
                print(f"Validated OK: {filename}")
                return_list.append((case_name, single_time, temp_object.PF_system.solving_information))
                # print("")
            except Exception as e:
                print(f"Validation failed for {filename}: {e}")
        
        print(f"All combinations processed; generated {i + 1} files.")
        return return_list


    def _multi_std_excels(self):
        """Enumerate variations with multiprocessing."""

        # print("Preparing data for parallel run...")
        
        region_keys = list(self.regions.keys())
        variant_ranges = []
        
        # --- A: pickle-friendly region payloads ---
        # Cannot send live SynGrid objects; send extracted dicts/lists
        # Serialize plain Python data only
        regions_data_structure = {}

        for region_key_ in region_keys:
            region = self.regions[region_key_]
            variant_count = len(region.syngrid_instance.variation_case)
            variant_ranges.append(range(variant_count))
            
            # Extract variation payloads
            # 1. variation_case entries
            # Trim heavy objects if needed
            raw_variations = region.syngrid_instance.variation_case
            
            # 2. std bus template for area/type
            std_data_bus = region.syngrid_instance.std_powercase.PF_system.data_dict['Bus']
            
            regions_data_structure[region_key_] = {
                'bus_map': region.bus_map,
                'variations': raw_variations,  # if huge, consider only data_dict
                'std_data_bus': std_data_bus
            }

        # print(f"Data ready; building {len(variant_ranges)}-D Cartesian product...")
        
        # --- B: build task list ---
        tasks = []
        # Ensure output directory
        save_dir = f"./CasesResult/GridCreateProject_{self.name}/variation/"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # Full Cartesian product
        all_combinations = list(itertools.product(*variant_ranges))
        total_cases = len(all_combinations)
        print(f"Total cases: {total_cases}. Starting process pool...")

        for i, combo in enumerate(all_combinations):
            task_args = (
                i, 
                combo, 
                region_keys, 
                regions_data_structure, 
                self.global_line_data, 
                self.name,
                save_dir,
                self.data_dict
            )
            tasks.append(task_args)

        # --- C: parallel execution ---
        # max_workers ~= CPU count
        # IO-heavy workloads may use slightly higher worker counts
        # CPU-heavy validation should stay near cpu_count()
        max_workers = min(os.cpu_count() or 1, 61)  # cap for Windows spawn limits
        
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # map preserves task order
            # PROCESS_SINGLE_CASE is top-level for pickling
            for result in executor.map(PROCESS_SINGLE_CASE, tasks):
                results.append(result)
                # Optional progress
                if len(results) % 100 == 0:
                    print(f"Progress: {len(results)}/{total_cases}")

        # print("\nParallel tasks finished. Sample log:")
        # for res in results[:5]:  # sample first 5
        #     print(res)
        print(f"All combinations processed; generated {i + 1} files.")
        return results  # optional return


    @staticmethod
    def _apply_alternating_row_colors(worksheet):
        """Apply alternating row fills below header."""
        from openpyxl.styles import PatternFill
        
        # Two alternating fills
        color1 = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        color2 = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        
        # Skip header row
        for row_idx, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
            fill_color = color1 if row_idx % 2 == 0 else color2
            for cell in row:
                cell.fill = fill_color


    @staticmethod
    def factorize_number(n: int, k: int):
        """
        Robust factorization helper handling edge cases.
        """
        if not isinstance(n, int) or not isinstance(k, int):
            raise TypeError("n and k must be integers")
        
        if n <= 0 or k <= 0:
            raise ValueError("n and k must be positive integers")
        
        if k == 1:
            return [n]
        
        # If k > n, pad with ones
        if k > n:
            # e.g. n=7, k=10 -> [1,1,1,1,1,1,1,7]
            return [1] * (k-1) + [n]
        
        # Prime n with k>1
        def is_prime(num):
            if num < 2:
                return False
            for i in range(2, int(math.sqrt(num)) + 1):
                if num % i == 0:
                    return False
            return True
        
        if is_prime(n) and k > 1:
            # Prime factorization fallback
            return [1] * (k-1) + [n]
        
        # Enumerate factor tuples
        def find_factors(num, count, start=2):
            """Recursive factor enumeration."""
            if count == 1:
                if num >= start:
                    return [[num]]
                return []
            
            result = []
            # Search ordered factors
            for i in range(start, int(math.sqrt(num)) + 1):
                if num % i == 0:
                    # Found divisor
                    sub_results = find_factors(num // i, count - 1, i)
                    for sub in sub_results:
                        result.append([i] + sub)
            
            return result
        
        # All k-factor products
        all_combinations = find_factors(n, k)
        
        if not all_combinations:
            # Pad with ones if needed
            # Reduce factor count
            for factor_count in range(k-1, 0, -1):
                combinations = find_factors(n, factor_count)
                if combinations:
                    best_combo = min(combinations, 
                                   key=lambda x: max(x) - min(x))
                    # Pad with ones
                    return sorted(best_combo + [1] * (k - factor_count))
            
            # Worst-case tuple
            return [1] * (k-1) + [n]
        
        # Pick lowest-variance tuple
        best_combo = None
        min_std = float('inf')
        
        for combo in all_combinations:
            mean = sum(combo) / len(combo)
            std = math.sqrt(sum((x - mean) ** 2 for x in combo) / len(combo))
            if std < min_std:
                min_std = std
                best_combo = combo
        
        return sorted(best_combo)


    def generate_grid(self, number=1, method='random', multi_process = False):
        """the main work flow of grid initialization"""
        if not isinstance(number, int):
            raise TypeError(f"number must be int; got {type(number).__name__}")
        
        if number < 1:
            raise ValueError(f"number must be positive; got {number}")
        # cumulative bus/branch offsets
        bus_offset = 0
        line_offset = 0
        
        for region_idx, region in sorted(self.regions.items()):
            # print(f"Building region {region_idx}: {region.name} ({region.size} buses)")
            
            if region.region_type == RegionType.AC:
                self._generate_ac_area(region, bus_offset, line_offset)
            else:
                self._generate_dc_area(region, bus_offset, line_offset)
            
            # advance offsets
            bus_offset += region.size
            line_offset += len(region.syngrid_instance.std_powercase.PF_system.data_dict['Network'])

        self._generate_ic_loc(method)
        std_powercase_0 = self.generate_power_flow()
        
        if number == 1:
            return std_powercase_0
        
        elif number>1:
            # region_num = 3 for example,
            region_num = len(self.regions.keys())
            # number = 100 for example, vary_list = [4, 5, 5] in this case
            vary_list = GridInit.factorize_number(number, region_num)
            # assign the vary_list to different regions
            region_keys = list(self.regions.keys())
            region_vary_dict = dict(zip(region_keys, vary_list))
            # loop to generate multiple cases
            for region_key, vary_num in region_vary_dict.items():
                self.regions[region_key].syngrid_instance.vary_case(vary_num)
            # validation
            elapsed_time, inner_results = self._generate_multi_power_flow(multi_process)
            self.multi_variation_information['total_time'] = elapsed_time
            self.multi_variation_information['inner_results'] = inner_results
            # plot convergence diagnostics
            self.saver.plot_convergence_curve(self.multi_variation_information)
            return self.multi_variation_information
            
            
    def _generate_multi_power_flow(self, multi_process):
        """only used for multiple cases"""
        start_time = time.time()  # time begin
        # enumerate variations + validate
        if multi_process:
            inner_results = self._multi_std_excels()
        else:
            inner_results = self._std_excels()
        end_time = time.time()  # end time
        elapsed_time = end_time - start_time
        return elapsed_time, inner_results


    def _generate_ic_loc(self, method):
        """generate ic location for ac-dc connection using optimization algorithm"""
        # instance for location
        self.ic_postion = ICPlacement()
        # create area group directly
        for converter_group in self.connections:
            # read endpoint regions
            from_info = self.regions[converter_group.from_region]
            to_info = self.regions[converter_group.to_region]
            
            # orient AC vs DC
            if from_info.region_type == RegionType.AC and to_info.region_type == RegionType.DC:
                ac_region, dc_region = from_info, to_info
                is_from_ac = True
            elif from_info.region_type == RegionType.DC and to_info.region_type == RegionType.AC:
                ac_region, dc_region = to_info, from_info
                is_from_ac = False
            else:
                print(f"Warning: Connection between same types {from_info.region_type} not fully optimized.")
                continue

            # PF data for placement
            # expect SynGrid instances
            if not ac_region.syngrid_instance:
                return random.randint(1, 10)  # fallback random IC bus
            if not dc_region.syngrid_instance:
                return random.randint(1, 10)  # fallback random IC bus
            ac_data = ac_region.syngrid_instance.std_powercase.PF_system.data_dict
            dc_data = dc_region.syngrid_instance.std_powercase.PF_system.data_dict
            
            # choose converter bus pairs
            num_converters = len(converter_group.converter_list)
            # respect occupied buses
            if method == 'random':
                best_pairs = self.ic_postion.select_random_pairs(
                    ac_data, dc_data, 
                    ac_region.converter_locations, 
                    dc_region.converter_locations, 
                    num_converters
                )
            if method == 'best':
                best_pairs = self.ic_postion.select_best_pairs(
                    ac_region.index, ac_data,     # pass AC region id + data
                    dc_region.index, dc_data,     # pass DC region id + data
                    ac_region.converter_locations, 
                    dc_region.converter_locations, 
                    num_converters
                )

            # assign pairs to converters
            for i, converter in enumerate(converter_group.converter_list):
                if i >= len(best_pairs):
                    break  # should not happen unless buses exhausted
                # local bus indices
                loc_ac, loc_dc = best_pairs[i]
                # track occupied buses
                ac_region.converter_locations.add(loc_ac)
                dc_region.converter_locations.add(loc_dc)
                # tag IC buses
                # mode defines PQ/PV mix
                control_mode = converter.mode
                ac_bus_type = GridInit.MODES_TYPE[control_mode][0]
                dc_bus_type = GridInit.MODES_TYPE[control_mode][1]
                # fill converter fields
                ac_bus_record = ac_data['Bus'][loc_ac - 1] 
                ac_bus_record['Type'] = ac_bus_type
                ac_bus_record['ACorDCorIC'] = 'ACIC'
                ac_bus_record['Apparatus'] = 'IC'
                ac_bus_record['Number'] = 1
                dc_bus_record = dc_data['Bus'][loc_dc - 1]
                dc_bus_record['Type'] = dc_bus_type
                dc_bus_record['ACorDCorIC'] = 'DCIC'
                dc_bus_record['Apparatus'] = 'IC'
                dc_bus_record['Number'] = 1

                # map to global bus numbers
                global_ac = ac_region.bus_map[loc_ac]
                global_dc = dc_region.bus_map[loc_dc]
                # store AC-side anchor
                if is_from_ac:
                    from_bus_global = global_ac
                    to_bus_global = global_dc
                    converter.bus = from_bus_global
                else:
                    from_bus_global = global_dc
                    to_bus_global = global_ac
                    converter.bus = to_bus_global
                
                # default IC parameters
                converter.C_bus = 0.008
                converter.Rg_pu = 0.005
                converter.Lg_pu = 7.5
                converter.f0 = 60
                # order endpoints for the tie line
                if from_bus_global < to_bus_global:
                    line_from, line_to = from_bus_global, to_bus_global
                else:
                    line_from, line_to = to_bus_global, from_bus_global
                # append inter-area branch
                line_data = {
                    'FromBus': line_from,
                    'ToBus': line_to,
                    'R (pu)': 0.1,
                    'X (pu)': 7.5,
                    'Turn': 1
                }
                self.global_line_data.append(line_data)


    def generate_power_flow(self):
        """perform power flow for parameters variation"""
        filepath = self._generate_std_excel()
        std_powercase = PowerCase(f"{self.name}", filepath, 'S')
        self.saver = PowerCaseResult(std_powercase.file_root)
        self.saver.draw_interconnected_topology(std_powercase.PF_system.agent_dict)
        # After PF: score + heatmap figures
        # figures under CasesResult
        plot_save_path = f"{self.saver.pic_dir}"
        # 1. regional score maps
        self.ic_postion.plot_region_scores(region_ids='all', save_path=plot_save_path)
        # 2. AC-DC link heatmaps
        self.ic_postion.plot_connection_heatmaps(save_path=plot_save_path)
        return std_powercase
