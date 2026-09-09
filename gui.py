"""
Graphical User Interface for Community Management System.

This module provides a complete Tkinter GUI for managing communities,
individuals, messages, skills, and services.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional
import psycopg2
from db_connection import get_connection

# Import all functions from main.py
from main import (
    view_community, view_message, view_proximity,
    search_people, search_communities, search_skills, search_services,
    add_individual, add_community, send_message, join_community,
    add_skill, add_entity_skill, add_service,
    connect_individuals, add_community_collaboration,
    view_individual_connections, view_community_collaborations,
    get_community_members, cast_exclusion_vote, get_exclusion_votes,
    get_exclusion_vote_stats
)


class CommunityManagementGUI:
    """Main GUI application for Community Management System."""
    
    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("Community Management System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Database connection
        self.conn = None
        self.connect_database()
        
        # Create main container
        self.create_widgets()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def connect_database(self):
        """Establish database connection."""
        try:
            self.conn = get_connection()
            self.status_message = "Database connected"
        except Exception as e:
            messagebox.showerror("Connection Error", 
                               f"Failed to connect to database:\n{e}")
            self.status_message = "Database connection failed"
            self.root.quit()
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Status bar
        self.status_bar = tk.Label(
            self.root, 
            text=self.status_message,
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            bg='#e0e0e0'
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_views_tab()
        self.create_search_tab()
        self.create_create_tab()
        self.create_connections_tab()
        self.create_exclusion_tab()
        
        # Results area (shared across tabs)
        self.create_results_area()
    
    def create_results_area(self):
        """Create results display area."""
        results_frame = tk.Frame(self.root, bg='#f0f0f0')
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results label
        self.results_label = tk.Label(
            results_frame, 
            text="Results will appear here",
            font=('Arial', 12, 'bold'),
            bg='#f0f0f0'
        )
        self.results_label.pack(anchor=tk.W, pady=5)
        
        # Treeview for results
        self.results_tree = ttk.Treeview(results_frame)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
    
    def clear_results(self):
        """Clear the results treeview."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
    
    def display_results(self, data, columns, title="Results"):
        """Display results in the treeview."""
        self.clear_results()
        self.results_label.config(text=f"{title} ({len(data)} items)")
        
        if not data:
            return
        
        # Configure columns
        self.results_tree['columns'] = columns
        self.results_tree['show'] = 'headings'
        
        # Configure column headers
        for col in columns:
            self.results_tree.heading(col, text=col.replace('_', ' ').title())
            self.results_tree.column(col, width=150, anchor=tk.W)
        
        # Insert data
        for row in data:
            values = [str(row.get(col, '')) for col in columns]
            self.results_tree.insert('', tk.END, values=values)
    
    def create_views_tab(self):
        """Create the Views tab."""
        views_frame = ttk.Frame(self.notebook)
        self.notebook.add(views_frame, text="Views")
        
        # Community View
        comm_frame = ttk.LabelFrame(views_frame, text="Community View", padding=10)
        comm_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(comm_frame, text="Individual ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.comm_individual_id = tk.Entry(comm_frame, width=20)
        self.comm_individual_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            comm_frame, 
            text="View Communities",
            command=self.show_community_view,
            bg='#4CAF50',
            fg='white',
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Message View
        msg_frame = ttk.LabelFrame(views_frame, text="Message View", padding=10)
        msg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(msg_frame, text="Entity ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.msg_entity_id = tk.Entry(msg_frame, width=20)
        self.msg_entity_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            msg_frame,
            text="View Messages",
            command=self.show_message_view,
            bg='#2196F3',
            fg='white',
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Proximity View
        prox_frame = ttk.LabelFrame(views_frame, text="Proximity View", padding=10)
        prox_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(prox_frame, text="Individual ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.prox_individual_id = tk.Entry(prox_frame, width=20)
        self.prox_individual_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(prox_frame, text="Max Distance (km):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.prox_distance = tk.Entry(prox_frame, width=20)
        self.prox_distance.insert(0, "1.0")
        self.prox_distance.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(
            prox_frame,
            text="View Proximity",
            command=self.show_proximity_view,
            bg='#FF9800',
            fg='white',
            width=20
        ).grid(row=1, column=2, padx=5, pady=5)
    
    def create_search_tab(self):
        """Create the Search tab."""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="Search")
        
        # Search People
        people_frame = ttk.LabelFrame(search_frame, text="Search People", padding=10)
        people_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(people_frame, text="Search term:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_people_entry = tk.Entry(people_frame, width=30)
        self.search_people_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            people_frame,
            text="Search",
            command=self.search_people_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Search Communities
        comm_frame = ttk.LabelFrame(search_frame, text="Search Communities", padding=10)
        comm_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(comm_frame, text="Search term:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_comm_entry = tk.Entry(comm_frame, width=30)
        self.search_comm_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            comm_frame,
            text="Search",
            command=self.search_communities_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Search Skills
        skills_frame = ttk.LabelFrame(search_frame, text="Search Skills", padding=10)
        skills_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(skills_frame, text="Search term:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_skills_entry = tk.Entry(skills_frame, width=30)
        self.search_skills_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            skills_frame,
            text="Search",
            command=self.search_skills_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Search Services
        services_frame = ttk.LabelFrame(search_frame, text="Search Services", padding=10)
        services_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(services_frame, text="Search term:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_services_entry = tk.Entry(services_frame, width=30)
        self.search_services_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            services_frame,
            text="Search",
            command=self.search_services_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=0, column=2, padx=5, pady=5)
    
    def create_create_tab(self):
        """Create the Create/Edit tab."""
        create_frame = ttk.Frame(self.notebook)
        self.notebook.add(create_frame, text="Create")
        
        # Scrollable frame
        canvas = tk.Canvas(create_frame, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(create_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add Individual
        self.create_add_individual_form(scrollable_frame)
        
        # Add Community
        self.create_add_community_form(scrollable_frame)
        
        # Send Message
        self.create_send_message_form(scrollable_frame)
        
        # Join Community
        self.create_join_community_form(scrollable_frame)
        
        # Add Skill
        self.create_add_skill_form(scrollable_frame)
        
        # Add Entity Skill
        self.create_add_entity_skill_form(scrollable_frame)
        
        # Add Service
        self.create_add_service_form(scrollable_frame)
        
        # Connect Individuals
        self.create_connect_individuals_form(scrollable_frame)
        
        # Add Community Collaboration
        self.create_add_collaboration_form(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_add_individual_form(self, parent):
        """Create form to add an individual."""
        frame = ttk.LabelFrame(parent, text="Add Individual", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Display Name:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_ind_name = tk.Entry(frame, width=25)
        self.add_ind_name.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Email:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_ind_email = tk.Entry(frame, width=25)
        self.add_ind_email.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Latitude (optional):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_ind_lat = tk.Entry(frame, width=25)
        self.add_ind_lat.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Longitude (optional):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_ind_lon = tk.Entry(frame, width=25)
        self.add_ind_lon.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Button(
            frame,
            text="Add Individual",
            command=self.add_individual_action,
            bg='#4CAF50',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    def create_add_community_form(self, parent):
        """Create form to add a community."""
        frame = ttk.LabelFrame(parent, text="Add Community", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Name:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_comm_name = tk.Entry(frame, width=25)
        self.add_comm_name.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Description (optional):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_comm_desc = tk.Entry(frame, width=25)
        self.add_comm_desc.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Button(
            frame,
            text="Add Community",
            command=self.add_community_action,
            bg='#4CAF50',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    def create_send_message_form(self, parent):
        """Create form to send a message."""
        frame = ttk.LabelFrame(parent, text="Send Message", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Sender ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.msg_sender_id = tk.Entry(frame, width=25)
        self.msg_sender_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Recipient ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.msg_recipient_id = tk.Entry(frame, width=25)
        self.msg_recipient_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Subject (optional):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.msg_subject = tk.Entry(frame, width=25)
        self.msg_subject.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Body (optional):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.msg_body = scrolledtext.ScrolledText(frame, width=25, height=3)
        self.msg_body.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Button(
            frame,
            text="Send Message",
            command=self.send_message_action,
            bg='#2196F3',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    def create_join_community_form(self, parent):
        """Create form to join a community."""
        frame = ttk.LabelFrame(parent, text="Join Community", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Individual ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.join_ind_id = tk.Entry(frame, width=25)
        self.join_ind_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Community ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.join_comm_id = tk.Entry(frame, width=25)
        self.join_comm_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        self.join_excluded = tk.BooleanVar()
        tk.Checkbutton(frame, text="Excluded", variable=self.join_excluded).grid(row=row, column=1, sticky=tk.W, padx=5)
        
        row += 1
        tk.Button(
            frame,
            text="Join Community",
            command=self.join_community_action,
            bg='#4CAF50',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    def create_add_skill_form(self, parent):
        """Create form to add a skill."""
        frame = ttk.LabelFrame(parent, text="Add Skill", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Label:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_skill_label = tk.Entry(frame, width=25)
        self.add_skill_label.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Description (optional):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_skill_desc = tk.Entry(frame, width=25)
        self.add_skill_desc.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Button(
            frame,
            text="Add Skill",
            command=self.add_skill_action,
            bg='#4CAF50',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    def create_add_entity_skill_form(self, parent):
        """Create form to associate skill with entity."""
        frame = ttk.LabelFrame(parent, text="Associate Skill with Entity", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Entity ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.entity_skill_entity_id = tk.Entry(frame, width=25)
        self.entity_skill_entity_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Skill ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.entity_skill_skill_id = tk.Entry(frame, width=25)
        self.entity_skill_skill_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Level (1-5):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.entity_skill_level = tk.Entry(frame, width=25)
        self.entity_skill_level.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Button(
            frame,
            text="Associate",
            command=self.add_entity_skill_action,
            bg='#4CAF50',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    def create_add_service_form(self, parent):
        """Create form to add a service."""
        frame = ttk.LabelFrame(parent, text="Add Service", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Entity ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_service_entity_id = tk.Entry(frame, width=25)
        self.add_service_entity_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Title:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_service_title = tk.Entry(frame, width=25)
        self.add_service_title.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Type (FREE/EXCHANGE/COMMERCIAL_G1):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_service_type = tk.Entry(frame, width=25)
        self.add_service_type.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Description (optional):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.add_service_desc = tk.Entry(frame, width=25)
        self.add_service_desc.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Button(
            frame,
            text="Add Service",
            command=self.add_service_action,
            bg='#4CAF50',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    def create_connect_individuals_form(self, parent):
        """Create form to connect two individuals."""
        frame = ttk.LabelFrame(parent, text="Connect Individuals", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Individual 1 ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.connect_ind1_id = tk.Entry(frame, width=25)
        self.connect_ind1_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Individual 2 ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.connect_ind2_id = tk.Entry(frame, width=25)
        self.connect_ind2_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Button(
            frame,
            text="Connect",
            command=self.connect_individuals_action,
            bg='#4CAF50',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    def create_add_collaboration_form(self, parent):
        """Create form to add community collaboration."""
        frame = ttk.LabelFrame(parent, text="Add Community Collaboration", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        tk.Label(frame, text="Community 1 ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.collab_comm1_id = tk.Entry(frame, width=25)
        self.collab_comm1_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Label(frame, text="Community 2 ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.collab_comm2_id = tk.Entry(frame, width=25)
        self.collab_comm2_id.grid(row=row, column=1, padx=5, pady=2)
        
        row += 1
        tk.Button(
            frame,
            text="Create Collaboration",
            command=self.add_collaboration_action,
            bg='#4CAF50',
            fg='white'
        ).grid(row=row, column=1, padx=5, pady=5)
    
    # Action methods for Views
    def show_community_view(self):
        """Display community view."""
        try:
            individual_id = int(self.comm_individual_id.get())
            results = view_community(self.conn, individual_id)
            
            if not results:
                messagebox.showinfo("No Results", "No communities found for this individual.")
                return
            
            columns = ['id_community', 'name', 'description', 'joinedat', 'isexcluded', 'total_members']
            self.display_results(results, columns, f"Communities for Individual {individual_id}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid individual ID.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def show_message_view(self):
        """Display message view."""
        try:
            entity_id = int(self.msg_entity_id.get())
            results = view_message(self.conn, entity_id)
            
            if not results:
                messagebox.showinfo("No Results", "No messages found for this entity.")
                return
            
            columns = ['id', 'sentat', 'subject', 'sender_name', 'recipient_name', 'inreplyto_id']
            self.display_results(results, columns, f"Messages for Entity {entity_id}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid entity ID.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def show_proximity_view(self):
        """Display proximity view."""
        try:
            individual_id = int(self.prox_individual_id.get())
            distance = self.prox_distance.get().strip()
            max_distance = float(distance) if distance else 1.0
            
            results = view_proximity(self.conn, individual_id, max_distance)
            
            if not results:
                messagebox.showinfo("No Results", "No individuals found in this radius.")
                return
            
            # Format results for display
            formatted_results = []
            for ind in results:
                formatted_results.append({
                    'id_individual': ind['id_individual'],
                    'displayname': ind['displayname'],
                    'email': ind['email'],
                    'latitude': f"{ind['latitude']:.6f}" if ind.get('latitude') else 'N/A',
                    'longitude': f"{ind['longitude']:.6f}" if ind.get('longitude') else 'N/A',
                    'distance_km': f"{ind['distance_km']:.2f}" if ind.get('distance_km') else 'N/A'
                })
            
            columns = ['id_individual', 'displayname', 'email', 'latitude', 'longitude', 'distance_km']
            self.display_results(formatted_results, columns, f"Proximity View for Individual {individual_id} ({max_distance} km)")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid individual ID and distance.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    # Action methods for Search
    def search_people_action(self):
        """Search for people."""
        search_term = self.search_people_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return
        
        try:
            results = search_people(self.conn, search_term)
            columns = ['id_individual', 'displayname', 'email', 'latitude', 'longitude']
            self.display_results(results, columns, f"Search Results: {search_term}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def search_communities_action(self):
        """Search for communities."""
        search_term = self.search_comm_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return
        
        try:
            results = search_communities(self.conn, search_term)
            columns = ['id_community', 'name', 'description', 'member_count']
            self.display_results(results, columns, f"Search Results: {search_term}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def search_skills_action(self):
        """Search for skills."""
        search_term = self.search_skills_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return
        
        try:
            results = search_skills(self.conn, search_term)
            columns = ['id', 'label', 'description', 'entity_count']
            self.display_results(results, columns, f"Search Results: {search_term}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def search_services_action(self):
        """Search for services."""
        search_term = self.search_services_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return
        
        try:
            results = search_services(self.conn, search_term)
            columns = ['id', 'title', 'type', 'description', 'provider_name']
            self.display_results(results, columns, f"Search Results: {search_term}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    # Action methods for Create
    def add_individual_action(self):
        """Add an individual."""
        try:
            name = self.add_ind_name.get().strip()
            email = self.add_ind_email.get().strip()
            
            if not name or not email:
                messagebox.showwarning("Warning", "Name and email are required.")
                return
            
            lat = self.add_ind_lat.get().strip()
            lon = self.add_ind_lon.get().strip()
            latitude = float(lat) if lat else None
            longitude = float(lon) if lon else None
            
            individual_id = add_individual(self.conn, name, email, latitude, longitude)
            messagebox.showinfo("Success", f"Individual created successfully!\nID: {individual_id}")
            
            # Clear form
            self.add_ind_name.delete(0, tk.END)
            self.add_ind_email.delete(0, tk.END)
            self.add_ind_lat.delete(0, tk.END)
            self.add_ind_lon.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Constraint violation: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def add_community_action(self):
        """Add a community."""
        try:
            name = self.add_comm_name.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Name is required.")
                return
            
            description = self.add_comm_desc.get().strip()
            description = description if description else None
            
            community_id = add_community(self.conn, name, description)
            messagebox.showinfo("Success", f"Community created successfully!\nID: {community_id}")
            
            # Clear form
            self.add_comm_name.delete(0, tk.END)
            self.add_comm_desc.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Constraint violation: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def send_message_action(self):
        """Send a message."""
        try:
            sender_id = int(self.msg_sender_id.get())
            recipient_id = int(self.msg_recipient_id.get())
            subject = self.msg_subject.get().strip()
            subject = subject if subject else None
            body = self.msg_body.get("1.0", tk.END).strip()
            body = body if body else None
            
            message_id = send_message(self.conn, sender_id, recipient_id, subject, body)
            messagebox.showinfo("Success", f"Message sent successfully!\nID: {message_id}")
            
            # Clear form
            self.msg_sender_id.delete(0, tk.END)
            self.msg_recipient_id.delete(0, tk.END)
            self.msg_subject.delete(0, tk.END)
            self.msg_body.delete("1.0", tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Constraint violation: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def join_community_action(self):
        """Join a community."""
        try:
            individual_id = int(self.join_ind_id.get())
            community_id = int(self.join_comm_id.get())
            is_excluded = self.join_excluded.get()
            
            membership_id = join_community(self.conn, individual_id, community_id, is_excluded)
            messagebox.showinfo("Success", f"Membership created successfully!\nID: {membership_id}")
            
            # Clear form
            self.join_ind_id.delete(0, tk.END)
            self.join_comm_id.delete(0, tk.END)
            self.join_excluded.set(False)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Constraint violation: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def add_skill_action(self):
        """Add a skill."""
        try:
            label = self.add_skill_label.get().strip()
            if not label:
                messagebox.showwarning("Warning", "Label is required.")
                return
            
            description = self.add_skill_desc.get().strip()
            description = description if description else None
            
            skill_id = add_skill(self.conn, label, description)
            messagebox.showinfo("Success", f"Skill created successfully!\nID: {skill_id}")
            
            # Clear form
            self.add_skill_label.delete(0, tk.END)
            self.add_skill_desc.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def add_entity_skill_action(self):
        """Associate skill with entity."""
        try:
            entity_id = int(self.entity_skill_entity_id.get())
            skill_id = int(self.entity_skill_skill_id.get())
            level = int(self.entity_skill_level.get())
            
            entity_skill_id = add_entity_skill(self.conn, entity_id, skill_id, level)
            messagebox.showinfo("Success", f"Association created successfully!\nID: {entity_skill_id}")
            
            # Clear form
            self.entity_skill_entity_id.delete(0, tk.END)
            self.entity_skill_skill_id.delete(0, tk.END)
            self.entity_skill_level.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Constraint violation: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def add_service_action(self):
        """Add a service."""
        try:
            entity_id = int(self.add_service_entity_id.get())
            title = self.add_service_title.get().strip()
            if not title:
                messagebox.showwarning("Warning", "Title is required.")
                return
            
            service_type = self.add_service_type.get().strip().upper()
            description = self.add_service_desc.get().strip()
            description = description if description else None
            
            service_id = add_service(self.conn, entity_id, title, service_type, description)
            messagebox.showinfo("Success", f"Service created successfully!\nID: {service_id}")
            
            # Clear form
            self.add_service_entity_id.delete(0, tk.END)
            self.add_service_title.delete(0, tk.END)
            self.add_service_type.delete(0, tk.END)
            self.add_service_desc.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Constraint violation: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def connect_individuals_action(self):
        """Connect two individuals."""
        try:
            ind1_id = int(self.connect_ind1_id.get())
            ind2_id = int(self.connect_ind2_id.get())
            
            connect_individuals(self.conn, ind1_id, ind2_id)
            messagebox.showinfo("Success", "Connection created successfully!")
            
            # Clear form
            self.connect_ind1_id.delete(0, tk.END)
            self.connect_ind2_id.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Constraint violation: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def add_collaboration_action(self):
        """Add community collaboration."""
        try:
            comm1_id = int(self.collab_comm1_id.get())
            comm2_id = int(self.collab_comm2_id.get())
            
            add_community_collaboration(self.conn, comm1_id, comm2_id)
            messagebox.showinfo("Success", "Collaboration created successfully!")
            
            # Clear form
            self.collab_comm1_id.delete(0, tk.END)
            self.collab_comm2_id.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Constraint violation: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def create_connections_tab(self):
        """Create the Connections tab."""
        conn_frame = ttk.Frame(self.notebook)
        self.notebook.add(conn_frame, text="Connections")
        
        # Individual Connections section
        ind_conn_frame = ttk.LabelFrame(conn_frame, text="Individual Connections", padding=10)
        ind_conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(ind_conn_frame, text="Individual ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.view_ind_conn_id = tk.Entry(ind_conn_frame, width=20)
        self.view_ind_conn_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            ind_conn_frame,
            text="View Connections",
            command=self.show_individual_connections,
            bg='#4CAF50',
            fg='white',
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Community Collaborations section
        comm_collab_frame = ttk.LabelFrame(conn_frame, text="Community Collaborations", padding=10)
        comm_collab_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(comm_collab_frame, text="Community ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.view_comm_collab_id = tk.Entry(comm_collab_frame, width=20)
        self.view_comm_collab_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            comm_collab_frame,
            text="View Collaborations",
            command=self.show_community_collaborations,
            bg='#2196F3',
            fg='white',
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
    
    def create_exclusion_tab(self):
        """Create the Exclusion Votes tab."""
        excl_frame = ttk.Frame(self.notebook)
        self.notebook.add(excl_frame, text="Exclusion Votes")
        
        # View members section
        members_frame = ttk.LabelFrame(excl_frame, text="View Community Members", padding=10)
        members_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(members_frame, text="Community ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.view_members_comm_id = tk.Entry(members_frame, width=20)
        self.view_members_comm_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            members_frame,
            text="View Members",
            command=self.show_community_members,
            bg='#4CAF50',
            fg='white',
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Cast vote section
        vote_frame = ttk.LabelFrame(excl_frame, text="Cast Exclusion Vote", padding=10)
        vote_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(vote_frame, text="Voter Individual ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.vote_voter_id = tk.Entry(vote_frame, width=20)
        self.vote_voter_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(vote_frame, text="Membership ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.vote_membership_id = tk.Entry(vote_frame, width=20)
        self.vote_membership_id.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(vote_frame, text="Vote (Exclude?):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.vote_choice = tk.BooleanVar()
        tk.Checkbutton(vote_frame, text="Yes, exclude", variable=self.vote_choice).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        tk.Button(
            vote_frame,
            text="Cast Vote",
            command=self.cast_vote_action,
            bg='#f44336',
            fg='white',
            width=20
        ).grid(row=2, column=2, padx=5, pady=5)
        
        # View votes section
        view_votes_frame = ttk.LabelFrame(excl_frame, text="View Exclusion Votes", padding=10)
        view_votes_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(view_votes_frame, text="Membership ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.view_votes_membership_id = tk.Entry(view_votes_frame, width=20)
        self.view_votes_membership_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            view_votes_frame,
            text="View Votes",
            command=self.show_exclusion_votes,
            bg='#FF9800',
            fg='white',
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
        
        tk.Button(
            view_votes_frame,
            text="View Vote Statistics",
            command=self.show_vote_stats,
            bg='#9C27B0',
            fg='white',
            width=20
        ).grid(row=0, column=3, padx=5, pady=5)
    
    def show_individual_connections(self):
        """Display individual connections."""
        try:
            individual_id = int(self.view_ind_conn_id.get())
            results = view_individual_connections(self.conn, individual_id)
            
            if not results:
                messagebox.showinfo("No Results", "No connections found for this individual.")
                return
            
            columns = ['connected_individual_id', 'connected_name', 'connected_email', 'latitude', 'longitude']
            self.display_results(results, columns, f"Connections for Individual {individual_id}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid individual ID.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def show_community_collaborations(self):
        """Display community collaborations."""
        try:
            community_id = int(self.view_comm_collab_id.get())
            results = view_community_collaborations(self.conn, community_id)
            
            if not results:
                messagebox.showinfo("No Results", "No collaborations found for this community.")
                return
            
            columns = ['collaborating_community_id', 'collaborating_name', 'collaborating_description']
            self.display_results(results, columns, f"Collaborations for Community {community_id}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid community ID.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def show_community_members(self):
        """Display community members."""
        try:
            community_id = int(self.view_members_comm_id.get())
            results = get_community_members(self.conn, community_id)
            
            if not results:
                messagebox.showinfo("No Results", "No members found for this community.")
                return
            
            columns = ['membership_id', 'id_individual', 'displayname', 'email', 'joinedat', 'isexcluded']
            self.display_results(results, columns, f"Members of Community {community_id}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid community ID.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def cast_vote_action(self):
        """Cast an exclusion vote."""
        try:
            voter_id = int(self.vote_voter_id.get())
            membership_id = int(self.vote_membership_id.get())
            vote = self.vote_choice.get()
            
            vote_id = cast_exclusion_vote(self.conn, voter_id, membership_id, vote)
            vote_text = "for exclusion" if vote else "against exclusion"
            messagebox.showinfo("Success", f"Vote cast successfully!\nVote ID: {vote_id}\nVoted {vote_text}")
            
            # Update the view votes field with the membership_id used
            self.view_votes_membership_id.delete(0, tk.END)
            self.view_votes_membership_id.insert(0, str(membership_id))
            
            # Clear form
            self.vote_voter_id.delete(0, tk.END)
            self.vote_membership_id.delete(0, tk.END)
            self.vote_choice.set(False)
            
            # Refresh vote stats
            self.show_vote_stats()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid value: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def show_exclusion_votes(self):
        """Display exclusion votes for a membership."""
        try:
            membership_id = int(self.view_votes_membership_id.get())
            results = get_exclusion_votes(self.conn, membership_id)
            
            if not results:
                messagebox.showinfo("No Results", "No votes found for this membership.")
                return
            
            columns = ['id', 'votedat', 'vote', 'individual_name', 'community_name']
            self.display_results(results, columns, f"Exclusion Votes for Membership {membership_id}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid membership ID.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def show_vote_stats(self, membership_id=None):
        """Display vote statistics."""
        try:
            if membership_id is None:
                membership_id_str = self.view_votes_membership_id.get().strip()
                if not membership_id_str:
                    messagebox.showwarning("Warning", "Please enter a membership ID.")
                    return
                membership_id = int(membership_id_str)
            
            stats = get_exclusion_vote_stats(self.conn, membership_id)
            
            if not stats:
                messagebox.showinfo("No Results", "Membership not found.")
                return
            
            stats_text = f"""
Vote Statistics for Membership {membership_id}

Individual: {stats['individual_name']} (ID: {stats['individual_id']})
Community: {stats['community_name']} (ID: {stats['community_id']})
Status: {'EXCLUDED' if stats['is_excluded'] else 'ACTIVE'}

Total Votes: {stats['total_votes']}
Votes FOR Exclusion: {stats['votes_for_exclusion']}
Votes AGAINST Exclusion: {stats['votes_against_exclusion']}

Total Community Members: {stats['total_members']}
Threshold for Exclusion: {stats['threshold']:.1f} votes

{'⚠️ EXCLUSION TRIGGERED' if stats['needs_exclusion'] and stats['is_excluded'] else '✓ Not excluded' if not stats['is_excluded'] else 'Pending exclusion'}
            """
            
            messagebox.showinfo("Vote Statistics", stats_text.strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid membership ID.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def on_closing(self):
        """Handle window closing."""
        if self.conn:
            self.conn.close()
        self.root.destroy()


def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = CommunityManagementGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

