import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button

# Global UI cleanup - prevents default Matplotlib hotkeys from interfering
plt.rcParams['keymap.fullscreen'] = []
plt.rcParams['keymap.home'] = []
plt.rcParams['keymap.back'] = []
plt.rcParams['keymap.forward'] = []

class InteractiveFirefighter:
    def __init__(self, H, root=None, hollow=True):
        # Close old figures to clear the backend state
        plt.close('all')
        
        self.H = H
        self.root = root
        self.protected = set()
        self.time = 0
        self.hollow = hollow
        self.history = []
        self.set_root_mode = False if root is not None else True
        
        # Position Setup
        self.pos = nx.get_node_attributes(H, 'pos')
        if not self.pos:
            if any(isinstance(n, tuple) and len(n) == 2 for n in H.nodes()):
                self.pos = {node: np.array(node) for node in H.nodes()}
            else:
                self.pos = nx.spring_layout(H, seed=42)
        
        # Figure Setup - Standard subplots for widget compatibility
        self.fig, self.ax = plt.subplots(figsize=(7, 9))
        self.fig.canvas.header_visible = False
        self.fig.canvas.footer_visible = False
        plt.subplots_adjust(top=0.82) 
        
        # UI BUTTONS
        ax_reset = plt.axes([0.05, 0.92, 0.15, 0.04])
        ax_back  = plt.axes([0.22, 0.92, 0.15, 0.04])
        ax_next  = plt.axes([0.39, 0.92, 0.15, 0.04])
        ax_mode  = plt.axes([0.60, 0.92, 0.35, 0.04])
        
        self.btn_reset = Button(ax_reset, 'Reset', color='#ff9999')
        self.btn_back  = Button(ax_back,  'Back',  color='#eeeeee')
        self.btn_next  = Button(ax_next,  'Next',  color='#99ff99')
        self.btn_mode  = Button(ax_mode, 'Mode: Set Root' if self.set_root_mode else 'Mode: Protect', color='#fdfd96')
        
        self.btn_reset.on_clicked(self.reset)
        self.btn_back.on_clicked(self.back)
        self.btn_next.on_clicked(self.next_turn)
        self.btn_mode.on_clicked(self.toggle_mode)
        
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        
        self.update_plot()

    def get_protected_nodes(self):
        """Returns current protected set."""
        return sorted(list(self.protected))
    
    def get_root(self):
        """Returns current fire origin."""
        return self.root

    def toggle_mode(self, event=None):
        self.set_root_mode = not self.set_root_mode
        self.btn_mode.label.set_text('Mode: Set Root' if self.set_root_mode else 'Mode: Protect')
        self.fig.canvas.draw_idle()

    def get_colors(self):
        if self.root is None:
            return ['black'] * len(self.H)
        S = {node for node in self.H if node not in self.protected}
        G = self.H.subgraph(S).copy()
        try:
            all_dists = dict(nx.shortest_path_length(G))
            r_dist = all_dists.get(self.root, {}).copy()
            none_root = S - nx.node_connected_component(G, self.root) if self.root in G else S
            for u in none_root:
                r_dist[u] = self.time + 1
        except:
            r_dist = {}
        
        colors = []
        for node in self.H:
            if node == self.root: colors.append('red')
            elif node in self.protected: colors.append('blue')
            elif r_dist.get(node, self.time + 1) <= self.time: colors.append('red')
            else: colors.append('black')
        return colors

    def update_plot(self):
        self.ax.clear()
        colors = self.get_colors()
        num_nodes = len(self.H.nodes())
        s_node = max(50, 5000 / num_nodes) if num_nodes > 36 else 600
        s_font = 8 if num_nodes < 100 else 0
        
        nx.draw(self.H, self.pos, ax=self.ax, with_labels=(self.hollow and s_font > 0),
                node_color='white' if self.hollow else colors,
                edgecolors=colors if self.hollow else None,
                linewidths=2, node_size=s_node, font_size=s_font, font_weight='bold')
        
        status = f"Fire Root: {self.root}" if self.root is not None else "Please set a Root"
        self.ax.set_title(f"Time: {self.time} | {status}\nProtected Nodes: {len(self.protected)}", pad=15)
        self.fig.canvas.draw_idle()

    def reset(self, event=None):
        self.time, self.protected, self.history = 0, set(), []
        self.update_plot()

    def back(self, event=None):
        if self.history:
            self.time, self.protected, self.root = self.history.pop()
            self.update_plot()

    def next_turn(self, event=None):
        if self.root is None: return
        self.history.append((self.time, self.protected.copy(), self.root))
        self.time += 1
        self.update_plot()

    def on_click(self, event):
        if event.inaxes != self.ax: return
        self.history.append((self.time, self.protected.copy(), self.root))
        click_xy = np.array([event.xdata, event.ydata])
        nodes = list(self.H.nodes())
        node_coords = np.array([self.pos[n] for n in nodes])
        dists = np.linalg.norm(node_coords - click_xy, axis=1)
        closest_node = nodes[np.argmin(dists)]
        
        if self.set_root_mode:
            self.root = closest_node
            if self.root in self.protected: self.protected.remove(self.root)
        else:
            if self.root is None or closest_node == self.root: return
            if closest_node in self.protected: self.protected.remove(closest_node)
            else:
                if self.get_colors()[nodes.index(closest_node)] == 'black':
                    self.protected.add(closest_node)
        self.update_plot()

    def on_key(self, event):
        if event.key.lower() == 'n': self.next_turn()


# ==========================================
# SAMPLE USAGE CODE
# ==========================================
# %matplotlib widget
# %load_ext autoreload
# %autoreload 2

# import networkx as nx
# from FF_Visual import InteractiveFirefighter
# from IPython.display import display


## Build the honeycomb grid
# H = nx.hexagonal_lattice_graph(4, 6)

## Launch (passing a specific root node if desired)
# ui = InteractiveFirefighter(H, root=(0, 0, 0), hollow=False)

## Display the interactive canvas
# display(ui.fig.canvas)

