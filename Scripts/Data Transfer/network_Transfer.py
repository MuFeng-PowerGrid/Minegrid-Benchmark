import sys
import json
import random
import os
import math

class Alpaca(object):
    """Alpaca"""
    
    def __init__(self):
        self.instruction = None
        self.input = None
        self.output = None

    def format(self):
        return {
                    "instruction": f"{self.instruction}",
                    "input": f"{self.input}",
                    "output": f"{self.output}"
                } 
    
    def format_value(self,val):
        """将值格式化为字符串，保留浮点数精度。"""
        if isinstance(val, float):
            # 使用 repr 保留尽可能多的精度
            return repr(val)
        elif isinstance(val, str):
            # 确保字符串被引号包裹，但为了可读性，我们不加额外引号
            return val
        else:
            return str(val)

    def format_item(self,item):
        """将字典的所有键值对格式化为 "key=value" 并用逗号连接。"""
        parts = []
        for k, v in item.items():
            parts.append(f"{k}={self.format_value(v)}")
        return ", ".join(parts)
    
    def map_item(self, item, instruction=None, output=None):
        """
        将任何电力系统参数转换为训练数据
        item: 可以是母线、线路、发电机、变换器等任何参数的字典
        """      
        # 自动检测参数类型
        param_type = self.detect_parameter_type(item)
        
        # 如果没有提供instruction，自动生成
        if instruction is None:
            instruction = self.generate_instruction(item, param_type)
        
        # 如果没有提供output，自动生成
        if output is None:
            output = self.generate_output(item, param_type)
        
        self.instruction = instruction
        self.input = self.format_item(item)  # 保持原有的参数格式
        self.output = output
        return self.format()
    
    def detect_parameter_type(self, item):
        """根据字典中的键自动检测参数类型"""
    
        # 定义各种参数类型的特征键
        type_signatures = {
            'bus': ['Bus', 'Type', 'PG', 'PL', 'Area No.', 'ACorDCorIC'],
            'network': ['FromBus', 'ToBus', 'R (pu)', 'X (pu)', 'Turn'],
            'ic': ['bus', 'mode', 'C_bus_pu', 'Rg_pu', 'Lg_pu', 'f0'],
            'gfl': ['bus', 'mode', 'C_bus', 'Rg_pu', 'Lg_pu', 'Ro_pu', 'Lo_pu', 'Cf_pu'],
            'gfm': ['bus', 'mode', 'C_bus_pu', 'Rg_pu', 'Lg_pu', 'Ro_pu', 'Lo_pu', 'Cf_pu'],
            'hsc': ['bus', 'C_bus_pu', 'Rg_pu', 'Lg_pu', 'P_od', 'I_od', 'P_oq', 'I_oq'],
            'hmc': ['bus', 'C_bus_pu', 'Rg_pu', 'Lg_pu', 'P_oq', 'I_oq', 'P_id', 'I_id', 'Kpu', 'Kiu'],
            'sg_s': [],  # 根据实际数据补充
            'sg_d': [],  # 根据实际数据补充
            'dcdc': [],  # 根据实际数据补充
            'im': [],    # 根据实际数据补充
        }
        
        # 检查item匹配哪种类型
        for param_type, signature in type_signatures.items():
            if signature:
                # 计算匹配度
                match_count = sum(1 for key in signature if key in item)
                if match_count >= len(signature) * 0.5:  # 50%匹配就算
                    return param_type
        
        return 'unknown'

# ========================================================================

    def generate_instruction(self, item, param_type):
        """根据参数类型生成指令"""
        
# 获取关键信息用于定制指令
        if param_type == 'bus':
            bus_num = item.get('Bus', '')
            bus_type = item.get('Type', '')
            type_desc = {1: "load", 2: "generator", 3: "swing"}.get(bus_type, "")
            
            templates = [
                f"Please analyze the electrical parameters of bus {bus_num}.",
                f"Bus {bus_num} is a {type_desc} node, please explain its operating status.",
                f"Describe the voltage, power and other parameters of bus {bus_num}.",
                f"Interpret the {type_desc} characteristics of bus {bus_num}.",
            ]
            
        elif param_type == 'network':
            from_bus = item.get('FromBus', '')
            to_bus = item.get('ToBus', '')
            
            templates = [
                f"Please analyze the line parameters from bus {from_bus} to bus {to_bus}.",
                f"What are the characteristics of this transmission line connecting bus {from_bus} and {to_bus}?",
                f"Explain the resistance and reactance values of this line.",
                f"Describe the impedance parameters of line {from_bus}-{to_bus}.",
            ]
            
        elif param_type == 'ic':
            bus = item.get('bus', '')
            mode = item.get('mode', '')
            mode_desc = {0: "rectifier", 1: "inverter", 2: "bidirectional", 3: "STATCOM"}.get(mode, f"mode {mode}")
            
            templates = [
                f"Please analyze the parameters of the Interlinking Converter (IC) connected to bus {bus}.",
                f"What are the parameters of this IC device operating in {mode_desc} mode?",
                f"Explain the control parameters of the IC converter at bus {bus}.",
            ]
            
        elif param_type == 'gfl':
            bus = item.get('bus', '')
            
            templates = [
                f"Please analyze the parameters of the Grid-Following (GFL) converter connected to bus {bus}.",
                f"What are the LCL filter parameters of this GFL device?",
                f"Describe the filter settings of the grid-following converter at bus {bus}.",
            ]
            
        elif param_type == 'gfm':
            bus = item.get('bus', '')
            
            templates = [
                f"Please analyze the parameters of the Grid-Forming (GFM) converter connected to bus {bus}.",
                f"What are the virtual synchronous machine parameters of this GFM device?",
                f"Describe the inertia support parameters of the grid-forming converter at bus {bus}.",
            ]
            
        elif param_type == 'hsc':
            bus = item.get('bus', '')
            
            templates = [
                f"Please analyze the parameters of the High-Bandwidth Converter (HSC) connected to bus {bus}.",
                f"What are the PI controller parameters of this HSC device?",
                f"Describe the control parameters of the high-bandwidth converter at bus {bus}.",
            ]
            
        elif param_type == 'hmc':
            bus = item.get('bus', '')
            
            templates = [
                f"Please analyze the parameters of the High-Bandwidth Motor Controller (HMC) connected to bus {bus}.",
                f"What are the motor control parameters of this HMC device?",
                f"Describe the PI parameters of the motor controller at bus {bus}.",
            ]
            
        else:
            # Unknown type, extract first few keys as reference
            keys = list(item.keys())[:3]
            templates = [
                f"Please analyze these power system parameters: {', '.join(keys)}, etc.",
                f"Explain the meaning of these electrical parameters.",
            ]
        
        return random.choice(templates)

    def generate_output(self, item, param_type):
        """根据参数类型生成详细的输出描述"""
        
        if param_type == 'bus':
            return self._generate_bus_output(item)
        elif param_type == 'network':
            return self._generate_network_output(item)
        elif param_type == 'ic':
            return self._generate_ic_output(item)
        elif param_type == 'gfl':
            return self._generate_gfl_output(item)
        elif param_type == 'gfm':
            return self._generate_gfm_output(item)
        elif param_type == 'hsc':
            return self._generate_hsc_output(item)
        elif param_type == 'hmc':
            return self._generate_hmc_output(item)
        else:
            return self._generate_generic_output(item)

    def _generate_bus_output(self, item):
        """Generate output description for bus parameters"""
        
        bus_num = item.get('Bus', '')
        bus_type = item.get('Type', '')
        base_kv = item.get('Base (kV)', 0)
        v = item.get('V', 1)
        theta = item.get('Theta', 0)
        pg = item.get('PG', 0)
        qg = item.get('QG', 0)
        pl = item.get('PL', 0)
        ql = item.get('QL', 0)
        area = item.get('Area No.', '')
        ac_dc = item.get('ACorDCorIC', '')
        
        # Bus type mapping
        type_map = {1: "load bus (PQ node)", 2: "generator bus (PV node)", 3: "slack bus (Vθ node)"}
        bus_type_str = type_map.get(bus_type, f"type {bus_type} node")
        
        # AC/DC type description
        ac_dc_desc = {
            "AC": "AC", "DC": "DC", 
            "ACIC": "AC interconnecting", "DCIC": "DC interconnecting"
        }.get(ac_dc, ac_dc)
        
        parts = [f"Bus {bus_num} is a {bus_type_str}, belonging to {ac_dc_desc} system, located in area {area}."]
        
        # Voltage information
        parts.append(f"Current voltage magnitude is {v:.3f} pu, phase angle is {theta} degrees.")
        
        # Generation information
        if pg != 0 or qg != 0:
            parts.append(f"Generation power: active {pg:.3f} pu, reactive {qg:.3f} pu.")
        
        # Load information
        if pl != 0 or ql != 0:
            parts.append(f"Load demand: active {pl:.3f} pu, reactive {ql:.3f} pu.")
        
        # Power limits
        qmin = item.get('Qmin', 0)
        qmax = item.get('Qmax', 0)
        pmin = item.get('Pmin', 0)
        pmax = item.get('Pmax', 0)
        
        if bus_type == 2:  # Generator bus
            parts.append(f"Reactive power limits: minimum {qmin:.2f} pu, maximum {qmax:.2f} pu.")
            if pg != 0:
                parts.append(f"Active power regulation range: {pg*pmin:.3f} pu to {pg*pmax:.3f} pu.")
        
        return " ".join(parts)

    def _generate_network_output(self, item):
        """Generate output description for line parameters"""
        
        from_bus = item.get('FromBus', '')
        to_bus = item.get('ToBus', '')
        r = item.get('R (pu)', 0)
        x = item.get('X (pu)', 0)
        turn = item.get('Turn', 1.0)
        
        # Calculate impedance magnitude and angle
        z = (r**2 + x**2)**0.5
        if r != 0:
            angle = math.degrees(math.atan(x/r))
        else:
            angle = 90 if x > 0 else -90
        
        # Determine line type
        if x > 10 * r:
            line_type = "highly inductive line"
            char = "has significant impact on reactive power transmission"
        elif r > 10 * x:
            line_type = "highly resistive line"
            char = "has significant impact on active power transmission"
        else:
            line_type = "normal resistive-inductive line"
            char = "affects both active and reactive power"
        
        # Special case (interconnecting line)
        if r == 0.1 and x == 7.5:
            line_type = "interconnecting line (IC connection)"
            char = "used to connect AC/DC systems in different areas"
        
        parts = [
            f"From bus {from_bus} to bus {to_bus} is a {line_type}, ",
            f"resistance is {r:.6f} pu, reactance is {x:.6f} pu, turn ratio is {turn:.3f}.",
            f"Impedance magnitude is {z:.6f} pu, impedance angle is {angle:.2f} degrees.",
            f"This line {char}."
        ]
        
        return " ".join(parts)

    def _generate_ic_output(self, item):
        """Generate output description for interlinking converter parameters"""
        
        bus = item.get('bus', '')
        mode = item.get('mode', '')
        c_bus = item.get('C_bus_pu', 0)
        rg = item.get('Rg_pu', 0)
        lg = item.get('Lg_pu', 0)
        f0 = item.get('f0', 60)
        
        mode_map = {0: "rectifier", 1: "inverter", 2: "bidirectional", 3: "STATCOM"}
        mode_str = mode_map.get(mode, f"unknown mode ({mode})")
        
        # Calculate characteristic frequency
        w_base = 2 * math.pi * f0
        lg_actual = lg / w_base if w_base != 0 else 0
        
        parts = [
            f"Interlinking Converter (IC) connected to bus {bus} operates in {mode_str} mode, with base frequency of {f0}Hz.",
            f"Bus support capacitance is {c_bus:.4f} pu, ",
            f"grid-side resistance is {rg:.4f} pu, grid-side inductance is {lg:.4f} pu."
        ]
        
        return " ".join(parts)

    def _generate_gfl_output(self, item):
        """Generate output description for grid-following converter parameters"""
        
        bus = item.get('bus', '')
        mode = item.get('mode', '')
        c_bus = item.get('C_bus', 0)
        rg = item.get('Rg_pu', 0)
        lg = item.get('Lg_pu', 0)
        ro = item.get('Ro_pu', 0)
        lo = item.get('Lo_pu', 0)
        cf = item.get('Cf_pu', 0)
        rf = item.get('Rf_pu', 0)
        f0 = item.get('f0', 60)
        
        parts = [
            f"Grid-Following Converter (GFL) connected to bus {bus} adopts LCL filter structure, ",
            f"grid-side inductance Lg={lg:.4f} pu, resistance Rg={rg:.4f} pu; ",
            f"converter-side inductance Lo={lo:.4f} pu, resistance Ro={ro:.4f} pu; ",
            f"filter capacitance Cf={cf:.6f} pu, damping resistance Rf={rf:.4f} pu; ",
            f"bus support capacitance C_bus={c_bus:.4f} pu, base frequency {f0}Hz."
        ]
        
        return " ".join(parts)

    def _generate_gfm_output(self, item):
        """Generate output description for grid-forming converter parameters"""
        
        bus = item.get('bus', '')
        mode = item.get('mode', '')
        c_bus = item.get('C_bus_pu', 0)
        rg = item.get('Rg_pu', 0)
        lg = item.get('Lg_pu', 0)
        ro = item.get('Ro_pu', 0)
        lo = item.get('Lo_pu', 0)
        cf = item.get('Cf_pu', 0)
        rf = item.get('Rf_pu', 0)
        f0 = item.get('f0', 60)
        
        parts = [
            f"Grid-Forming Converter (GFM) connected to bus {bus} simulates synchronous generator characteristics, ",
            f"output filter parameters: Lg={lg:.4f} pu, Rg={rg:.4f} pu, ",
            f"Lo={lo:.4f} pu, Ro={ro:.4f} pu, Cf={cf:.6f} pu, Rf={rf:.4f} pu, ",
            f"bus support capacitance C_bus={c_bus:.4f} pu, base frequency {f0}Hz."
        ]
        
        return " ".join(parts)

    def _generate_hsc_output(self, item):
        """Generate output description for high-bandwidth converter parameters"""
        
        bus = item.get('bus', '')
        c_bus = item.get('C_bus_pu', 0)
        rg = item.get('Rg_pu', 0)
        lg = item.get('Lg_pu', 0)
        p_od = item.get('P_od', 0)
        i_od = item.get('I_od', 0)
        p_oq = item.get('P_oq', 0)
        i_oq = item.get('I_oq', 0)
        p_id = item.get('P_id', 0)
        i_id = item.get('I_id', 0)
        p_iq = item.get('P_iq', 0)
        i_iq = item.get('I_iq', 0)
        p_pll = item.get('P_pll', 0)
        i_pll = item.get('I_pll', 0)
        f0 = item.get('f0', 60)
        
        parts = [
            f"High-Bandwidth Converter (HSC) connected to bus {bus} has fast response characteristics, ",
            f"voltage loop PI parameters: P={p_od:.2f}, I={i_od:.2f}; ",
            f"current loop PI parameters: P={p_oq:.2f}, I={i_oq:.2f}; ",
            f"Phase-Locked Loop (PLL) parameters: P={p_pll:.2f}, I={i_pll:.2f}; ",
            f"grid-side impedance: Rg={rg:.4f} pu, Lg={lg:.4f} pu, ",
            f"bus capacitance C_bus={c_bus:.4f} pu, base frequency {f0}Hz."
        ]
        
        return " ".join(parts)

    def _generate_hmc_output(self, item):
        """Generate output description for high-bandwidth motor controller parameters"""
        
        bus = item.get('bus', '')
        c_bus = item.get('C_bus_pu', 0)
        rg = item.get('Rg_pu', 0)
        lg = item.get('Lg_pu', 0)
        p_oq = item.get('P_oq', 0)
        i_oq = item.get('I_oq', 0)
        p_id = item.get('P_id', 0)
        i_id = item.get('I_id', 0)
        p_iq = item.get('P_iq', 0)
        i_iq = item.get('I_iq', 0)
        p_pll = item.get('P_pll', 0)
        i_pll = item.get('I_pll', 0)
        kpu = item.get('Kpu', 0)
        kiu = item.get('Kiu', 0)
        kpi = item.get('Kpi', 0)
        kii = item.get('Kii', 0)
        f0 = item.get('f0', 60)
        
        parts = [
            f"High-Bandwidth Motor Controller (HMC) connected to bus {bus} is used for motor drive, ",
            f"voltage loop PI parameters: Kpu={kpu:.2f}, Kiu={kiu:.2f}; ",
            f"current loop PI parameters: Kpi={kpi:.2f}, Kii={kii:.2f}; ",
            f"grid-side impedance: Rg={rg:.4f} pu, Lg={lg:.4f} pu, ",
            f"bus capacitance C_bus={c_bus:.4f} pu, base frequency {f0}Hz."
        ]
        
        return " ".join(parts)

    def _generate_generic_output(self, item):
        """Generate output description for generic parameters"""
        
        parts = ["Parameter details: "]
        for key, value in item.items():
            if isinstance(value, float):
                if abs(value) < 0.001:
                    parts.append(f"{key}={value:.6f}")
                else:
                    parts.append(f"{key}={value:.4f}")
            else:
                parts.append(f"{key}={value}")
        
        return "，".join(parts) + "。"

    def format_item(self, item):
        """Format a single dictionary as an input string"""
        return ", ".join([f"{k}={v}" for k, v in item.items()])


alpaca = Alpaca()

def generate_json(source_file, n):
    """Read data from source_file, apply corresponding mapping function to each existing section, and write to target_file."""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: JSON parsing failed - {e}")
        sys.exit(1)

    if not isinstance(source_data, dict):
        print("Error: Source JSON should be in dictionary format.")
        sys.exit(1)

    # Create data storage folder
    os.makedirs(f".\Database\\jsondata\\json{n}", exist_ok=True)

    for section in list(source_data.keys()):
        target_data = []        
        # Write to target file
        try:
            with open(f".\Database\\jsondata\\json{n}\\{section}.json", 'w', encoding='utf-8') as f:
                items = source_data[section]
                if isinstance(items, list):
                    for item in items:
                        if random.randint(0, 2) == 0:
                            target_data.append(alpaca.map_item(item))
                else:
                    print(f"Warning: Section '{section}' is not a list, skipped.")

                json.dump(target_data, f, ensure_ascii=False, indent=2)
            print(f"Successfully generated {len(target_data)} records, saved to Performer\\Database\\json\\{section}.json")
        except Exception as e:
            print(f"Error writing to target file: {e}")
            sys.exit(1)
            
if __name__ == "__main__":
 
    source_file = "------------"   # Default source file name

    generate_json(source_file)