"""
User Interface for Community Management System.

This module provides a user-friendly GUI for logged-in users to manage
their communities, messages, skills, and services.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date
from db_connection import get_connection

# Import functions from main.py
from main import (
    view_community, view_message, view_proximity,
    search_communities, search_skills, search_services,
    send_message, join_community, leave_community,
    add_skill, add_entity_skill, add_service, get_next_id,
    view_individual_connections, view_community_collaborations,
    get_community_members, cast_exclusion_vote, get_exclusion_votes,
    get_exclusion_vote_stats
)


def get_recent_messages(conn, entity_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Gets recent messages received by an entity.
    
    Args:
        conn: Database connection
        entity_id: ID of the entity
        limit: Maximum number of messages to return
        
    Returns:
        List of recent messages
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                m.id,
                m.SentAt,
                m.Subject,
                m.body,
                e.displayName as sender_name,
                m.sender_id,
                m.InReplyTo_id
            FROM Message m
            JOIN Entity e ON m.sender_id = e.id
            WHERE m.recipient_id = %s
            ORDER BY m.SentAt DESC
            LIMIT %s
        """, (entity_id, limit))
        return cur.fetchall()


def get_my_skills(conn, entity_id: int) -> List[Dict[str, Any]]:
    """
    Gets all skills associated with an entity.
    
    Args:
        conn: Database connection
        entity_id: ID of the entity
        
    Returns:
        List of skills with levels
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                s.id,
                s.label,
                s.description,
                es.level
            FROM EntitySkill es
            JOIN Skill s ON es.skill_id = s.id
            WHERE es.entity_id = %s
            ORDER BY s.label
        """, (entity_id,))
        return cur.fetchall()


def get_my_services(conn, entity_id: int) -> List[Dict[str, Any]]:
    """
    Gets all services offered by an entity.
    
    Args:
        conn: Database connection
        entity_id: ID of the entity
        
    Returns:
        List of services
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                s.id,
                s.title,
                s.type,
                s.description
            FROM Service s
            WHERE s.entity_id = %s
            ORDER BY s.title
        """, (entity_id,))
        return cur.fetchall()


def get_user_info(conn, individual_id: int) -> Optional[Dict[str, Any]]:
    """
    Gets user information.
    
    Args:
        conn: Database connection
        individual_id: ID of the individual
        
    Returns:
        User information dictionary or None
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                i.id_individual,
                e.displayName,
                i.email,
                CAST(i.latitude AS FLOAT) / 1000000.0 as latitude,
                CAST(i.longitude AS FLOAT) / 1000000.0 as longitude
            FROM Individual i
            JOIN Entity e ON i.id_individual = e.id
            WHERE i.id_individual = %s
        """, (individual_id,))
        return cur.fetchone()


class UserInterface:
    """User interface for logged-in users."""
    
    def __init__(self, root):
        """Initialize the user interface."""
        self.root = root
        self.root.title("Community Management - User Portal")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Current user
        self.current_user_id = None
        self.current_user_info = None
        
        # Database connection
        self.conn = None
        self.connect_database()
        
        # Create login screen first
        self.create_login_screen()
        
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
    
    def create_login_screen(self):
        """Create the login screen."""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        login_frame = tk.Frame(self.root, bg='#f0f0f0')
        login_frame.pack(expand=True)
        
        tk.Label(
            login_frame,
            text="Community Management System",
            font=('Arial', 24, 'bold'),
            bg='#f0f0f0'
        ).pack(pady=30)
        
        tk.Label(
            login_frame,
            text="User Login",
            font=('Arial', 16),
            bg='#f0f0f0'
        ).pack(pady=20)
        
        input_frame = tk.Frame(login_frame, bg='#f0f0f0')
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Individual ID:", font=('Arial', 12), bg='#f0f0f0').grid(row=0, column=0, padx=10, pady=10)
        self.login_id_entry = tk.Entry(input_frame, width=30, font=('Arial', 12))
        self.login_id_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Button(
            input_frame,
            text="Login",
            command=self.login,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=15,
            height=2
        ).grid(row=1, column=0, columnspan=2, pady=20)
    
    def login(self):
        """Handle user login."""
        try:
            user_id = int(self.login_id_entry.get())
            user_info = get_user_info(self.conn, user_id)
            
            if not user_info:
                messagebox.showerror("Login Error", "User not found. Please check your ID.")
                return
            
            self.current_user_id = user_id
            self.current_user_info = user_info
            self.create_main_interface()
            
        except ValueError:
            messagebox.showerror("Login Error", "Please enter a valid ID.")
        except Exception as e:
            messagebox.showerror("Login Error", f"An error occurred: {e}")
    
    def create_main_interface(self):
        """Create the main user interface."""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Header with user info
        header_frame = tk.Frame(self.root, bg='#2196F3', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        user_info_text = f"Logged in as: {self.current_user_info['displayname']} (ID: {self.current_user_id})"
        tk.Label(
            header_frame,
            text=user_info_text,
            font=('Arial', 14, 'bold'),
            bg='#2196F3',
            fg='white'
        ).pack(side=tk.LEFT, padx=20, pady=20)
        
        tk.Button(
            header_frame,
            text="Logout",
            command=self.logout,
            bg='#f44336',
            fg='white',
            font=('Arial', 10),
            width=10
        ).pack(side=tk.RIGHT, padx=20, pady=20)
        
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
        
        # Create main container with notebook and results
        main_container = tk.Frame(self.root)
        # reduced top padding so results get closer to notebook
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 0))
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main_container)
        # remove extra vertical gap under notebook
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 2))
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_communities_tab()
        self.create_messages_tab()
        self.create_skills_tab()
        self.create_services_tab()
        self.create_proximity_tab()
        self.create_connections_tab()
        self.create_exclusion_tab()
        
        # Results area
        self.create_results_area(main_container)
    
    def create_results_area(self, parent):
        """Create results display area."""
        results_frame = tk.Frame(parent, bg='#f0f0f0')
        # reduce vertical spacing to bring it closer to notebook above
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        self.results_label = tk.Label(
            results_frame,
            text="Results will appear here",
            font=('Arial', 12, 'bold'),
            bg='#f0f0f0'
        )
        # smaller top padding
        self.results_label.pack(anchor=tk.W, pady=2)
        
        # Treeview for results
        self.results_tree = ttk.Treeview(results_frame)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
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
        
        self.results_tree['columns'] = columns
        self.results_tree['show'] = 'headings'
        
        for col in columns:
            self.results_tree.heading(col, text=col.replace('_', ' ').title())
            self.results_tree.column(col, width=150, anchor=tk.W)
        
        for row in data:
            values = [str(row.get(col, '')) for col in columns]
            self.results_tree.insert('', tk.END, values=values)
    
    def create_dashboard_tab(self):
        """Create the dashboard tab."""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Welcome message
        welcome_frame = tk.Frame(dashboard_frame, bg='#f0f0f0')
        welcome_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(
            welcome_frame,
            text=f"Welcome, {self.current_user_info['displayname']}!",
            font=('Arial', 18, 'bold'),
            bg='#f0f0f0'
        ).pack()
        
        # Quick stats
        stats_frame = ttk.LabelFrame(dashboard_frame, text="Quick Stats", padding=20)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Get user stats
        my_communities = view_community(self.conn, self.current_user_id)
        my_skills = get_my_skills(self.conn, self.current_user_id)
        my_services = get_my_services(self.conn, self.current_user_id)
        recent_messages = get_recent_messages(self.conn, self.current_user_id, limit=5)
        my_connections = view_individual_connections(self.conn, self.current_user_id)
        
        stats_text = f"""
        My Communities: {len(my_communities)}
        My Connections: {len(my_connections)}
        My Skills: {len(my_skills)}
        My Services: {len(my_services)}
        Recent Messages: {len(recent_messages)}
        """
        
        tk.Label(
            stats_frame,
            text=stats_text.strip(),
            font=('Arial', 12),
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dashboard_frame, text="Quick Actions", padding=20)
        actions_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(
            actions_frame,
            text="View My Communities",
            command=lambda: self.show_my_communities(),
            bg='#4CAF50',
            fg='white',
            width=25,
            height=2
        ).grid(row=0, column=0, padx=10, pady=5)
        
        tk.Button(
            actions_frame,
            text="View Recent Messages",
            command=lambda: self.show_recent_messages(),
            bg='#2196F3',
            fg='white',
            width=25,
            height=2
        ).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Button(
            actions_frame,
            text="View My Skills",
            command=lambda: self.show_my_skills(),
            bg='#FF9800',
            fg='white',
            width=25,
            height=2
        ).grid(row=1, column=0, padx=10, pady=5)
        
        tk.Button(
            actions_frame,
            text="View My Services",
            command=lambda: self.show_my_services(),
            bg='#9C27B0',
            fg='white',
            width=25,
            height=2
        ).grid(row=1, column=1, padx=10, pady=5)
        
        tk.Button(
            actions_frame,
            text="View My Connections",
            command=lambda: self.show_my_connections(),
            bg='#00BCD4',
            fg='white',
            width=25,
            height=2
        ).grid(row=2, column=0, padx=10, pady=5)
    
    def create_communities_tab(self):
        """Create the communities tab."""
        comm_frame = ttk.Frame(self.notebook)
        self.notebook.add(comm_frame, text="Communities")
        
        # My Communities section
        my_comm_frame = ttk.LabelFrame(comm_frame, text="My Communities", padding=10)
        my_comm_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            my_comm_frame,
            text="Refresh My Communities",
            command=self.show_my_communities,
            bg='#4CAF50',
            fg='white',
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        # Leave community section
        leave_frame = ttk.LabelFrame(comm_frame, text="Leave a Community", padding=10)
        leave_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(leave_frame, text="Community ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.leave_comm_id = tk.Entry(leave_frame, width=20)
        self.leave_comm_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            leave_frame,
            text="Leave Community",
            command=self.leave_community_action,
            bg='#f44336',
            fg='white',
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Search Communities section
        search_frame = ttk.LabelFrame(comm_frame, text="Search Communities", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search term:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_comm_entry = tk.Entry(search_frame, width=30)
        self.search_comm_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            search_frame,
            text="Search",
            command=self.search_communities_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Join community section
        join_frame = ttk.LabelFrame(comm_frame, text="Join a Community", padding=10)
        join_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(join_frame, text="Community ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.join_comm_id = tk.Entry(join_frame, width=20)
        self.join_comm_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            join_frame,
            text="Join Community",
            command=self.join_community_action,
            bg='#4CAF50',
            fg='white',
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
    
    def create_messages_tab(self):
        """Create the messages tab."""
        msg_frame = ttk.Frame(self.notebook)
        self.notebook.add(msg_frame, text="Messages")
        
        # View messages section
        view_frame = ttk.LabelFrame(msg_frame, text="View Messages", padding=10)
        view_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            view_frame,
            text="View All My Messages",
            command=self.show_all_messages,
            bg='#2196F3',
            fg='white',
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            view_frame,
            text="View Recent Messages",
            command=self.show_recent_messages,
            bg='#2196F3',
            fg='white',
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        # Send message section
        send_frame = ttk.LabelFrame(msg_frame, text="Send a Message", padding=10)
        send_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(send_frame, text="Recipient ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.send_msg_recipient_id = tk.Entry(send_frame, width=20)
        self.send_msg_recipient_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(send_frame, text="Subject:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.send_msg_subject = tk.Entry(send_frame, width=50)
        self.send_msg_subject.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        
        tk.Label(send_frame, text="Message:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.send_msg_body = scrolledtext.ScrolledText(send_frame, width=50, height=5)
        self.send_msg_body.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
        
        tk.Label(send_frame, text="Reply to Message ID (optional):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.send_msg_reply_to = tk.Entry(send_frame, width=20)
        self.send_msg_reply_to.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Button(
            send_frame,
            text="Send Message",
            command=self.send_message_action,
            bg='#4CAF50',
            fg='white',
            width=20
        ).grid(row=3, column=2, padx=5, pady=5)
    
    def create_skills_tab(self):
        """Create the skills tab."""
        skills_frame = ttk.Frame(self.notebook)
        self.notebook.add(skills_frame, text="Skills")
        
        # My Skills section
        my_skills_frame = ttk.LabelFrame(skills_frame, text="My Skills", padding=10)
        my_skills_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            my_skills_frame,
            text="View My Skills",
            command=self.show_my_skills,
            bg='#FF9800',
            fg='white',
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        # Search Skills section
        search_frame = ttk.LabelFrame(skills_frame, text="Search Skills", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search term:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_skills_entry = tk.Entry(search_frame, width=30)
        self.search_skills_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            search_frame,
            text="Search",
            command=self.search_skills_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Add Skill section
        add_skill_frame = ttk.LabelFrame(skills_frame, text="Add New Skill", padding=10)
        add_skill_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(add_skill_frame, text="Skill Label:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.add_skill_label = tk.Entry(add_skill_frame, width=30)
        self.add_skill_label.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(add_skill_frame, text="Description (optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.add_skill_desc = tk.Entry(add_skill_frame, width=30)
        self.add_skill_desc.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(
            add_skill_frame,
            text="Add Skill",
            command=self.add_skill_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # Associate Skill section
        assoc_frame = ttk.LabelFrame(skills_frame, text="Add Skill to My Profile", padding=10)
        assoc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(assoc_frame, text="Skill ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.assoc_skill_id = tk.Entry(assoc_frame, width=20)
        self.assoc_skill_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(assoc_frame, text="Level (1-5):").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.assoc_skill_level = tk.Entry(assoc_frame, width=10)
        self.assoc_skill_level.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Button(
            assoc_frame,
            text="Add to My Profile",
            command=self.add_skill_to_profile_action,
            bg='#4CAF50',
            fg='white',
            width=20
        ).grid(row=0, column=4, padx=5, pady=5)
    
    def create_services_tab(self):
        """Create the services tab."""
        services_frame = ttk.Frame(self.notebook)
        self.notebook.add(services_frame, text="Services")
        
        # My Services section
        my_services_frame = ttk.LabelFrame(services_frame, text="My Services", padding=10)
        my_services_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            my_services_frame,
            text="View My Services",
            command=self.show_my_services,
            bg='#9C27B0',
            fg='white',
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        # Search Services section
        search_frame = ttk.LabelFrame(services_frame, text="Search Services", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search term:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_services_entry = tk.Entry(search_frame, width=30)
        self.search_services_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            search_frame,
            text="Search",
            command=self.search_services_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Add Service section
        add_service_frame = ttk.LabelFrame(services_frame, text="Add a Service", padding=10)
        add_service_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(add_service_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.add_service_title = tk.Entry(add_service_frame, width=30)
        self.add_service_title.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(add_service_frame, text="Type (FREE/EXCHANGE/COMMERCIAL_G1):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.add_service_type = tk.Entry(add_service_frame, width=30)
        self.add_service_type.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(add_service_frame, text="Description (optional):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.add_service_desc = tk.Entry(add_service_frame, width=30)
        self.add_service_desc.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Button(
            add_service_frame,
            text="Add Service",
            command=self.add_service_action,
            bg='#4CAF50',
            fg='white',
            width=15
        ).grid(row=2, column=2, padx=5, pady=5)
    
    def create_proximity_tab(self):
        """Create the proximity tab."""
        prox_frame = ttk.Frame(self.notebook)
        self.notebook.add(prox_frame, text="Proximity")
        
        # Proximity View section
        view_frame = ttk.LabelFrame(prox_frame, text="Find Nearby People", padding=10)
        view_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(view_frame, text="Max Distance (km):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.prox_distance = tk.Entry(view_frame, width=20)
        self.prox_distance.insert(0, "1.0")
        self.prox_distance.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            view_frame,
            text="Find Nearby People",
            command=self.show_proximity_view,
            bg='#FF9800',
            fg='white',
            width=25
        ).grid(row=0, column=2, padx=5, pady=5)
    
    # Action methods
    def show_my_communities(self):
        """Display user's communities."""
        try:
            results = view_community(self.conn, self.current_user_id)
            columns = ['id_community', 'name', 'description', 'joinedat', 'isexcluded', 'total_members']
            self.display_results(results, columns, "My Communities")
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
    
    def join_community_action(self):
        """Join a community."""
        try:
            community_id = int(self.join_comm_id.get())
            membership_id = join_community(self.conn, self.current_user_id, community_id, False)
            messagebox.showinfo("Success", f"Successfully joined community!\nMembership ID: {membership_id}")
            self.join_comm_id.delete(0, tk.END)
            self.show_my_communities()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid community ID.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Error: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def leave_community_action(self):
        """Leave a community."""
        try:
            community_id = int(self.leave_comm_id.get())
            if leave_community(self.conn, self.current_user_id, community_id):
                messagebox.showinfo("Success", "Successfully left the community!")
                self.leave_comm_id.delete(0, tk.END)
                self.show_my_communities()
            else:
                messagebox.showwarning("Warning", "You are not a member of this community.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid community ID.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def show_all_messages(self):
        """Display all user messages."""
        try:
            results = view_message(self.conn, self.current_user_id)
            columns = ['id', 'sentat', 'subject', 'sender_name', 'recipient_name', 'inreplyto_id']
            self.display_results(results, columns, "All My Messages")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def show_recent_messages(self):
        """Display recent messages."""
        try:
            results = get_recent_messages(self.conn, self.current_user_id, limit=20)
            columns = ['id', 'sentat', 'subject', 'sender_name', 'sender_id']
            self.display_results(results, columns, "Recent Messages Received")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def send_message_action(self):
        """Send a message."""
        try:
            recipient_id = int(self.send_msg_recipient_id.get())
            subject = self.send_msg_subject.get().strip()
            subject = subject if subject else None
            body = self.send_msg_body.get("1.0", tk.END).strip()
            body = body if body else None
            
            reply_to = self.send_msg_reply_to.get().strip()
            reply_to_id = int(reply_to) if reply_to else None
            
            message_id = send_message(self.conn, self.current_user_id, recipient_id, subject, body, reply_to_id)
            messagebox.showinfo("Success", f"Message sent successfully!\nMessage ID: {message_id}")
            
            # Clear form
            self.send_msg_recipient_id.delete(0, tk.END)
            self.send_msg_subject.delete(0, tk.END)
            self.send_msg_body.delete("1.0", tk.END)
            self.send_msg_reply_to.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Please enter valid IDs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Error: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def show_my_skills(self):
        """Display user's skills."""
        try:
            results = get_my_skills(self.conn, self.current_user_id)
            columns = ['id', 'label', 'description', 'level']
            self.display_results(results, columns, "My Skills")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def search_skills_action(self):
        """Search for skills."""
        search_term = self.search_skills_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return
        
        try:
            from main import search_skills
            results = search_skills(self.conn, search_term)
            columns = ['id', 'label', 'description', 'entity_count']
            self.display_results(results, columns, f"Search Results: {search_term}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def add_skill_action(self):
        """Add a new skill to the system."""
        try:
            from main import add_skill
            label = self.add_skill_label.get().strip()
            if not label:
                messagebox.showwarning("Warning", "Label is required.")
                return
            
            description = self.add_skill_desc.get().strip()
            description = description if description else None
            
            skill_id = add_skill(self.conn, label, description)
            messagebox.showinfo("Success", f"Skill created successfully!\nSkill ID: {skill_id}")
            
            self.add_skill_label.delete(0, tk.END)
            self.add_skill_desc.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def add_skill_to_profile_action(self):
        """Add a skill to user's profile."""
        try:
            skill_id = int(self.assoc_skill_id.get())
            level = int(self.assoc_skill_level.get())
            
            entity_skill_id = add_entity_skill(self.conn, self.current_user_id, skill_id, level)
            messagebox.showinfo("Success", f"Skill added to your profile!\nAssociation ID: {entity_skill_id}")
            
            self.assoc_skill_id.delete(0, tk.END)
            self.assoc_skill_level.delete(0, tk.END)
            self.show_my_skills()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid skill ID and level (1-5).")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Error: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def show_my_services(self):
        """Display user's services."""
        try:
            results = get_my_services(self.conn, self.current_user_id)
            columns = ['id', 'title', 'type', 'description']
            self.display_results(results, columns, "My Services")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def search_services_action(self):
        """Search for services."""
        search_term = self.search_services_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return
        
        try:
            from main import search_services
            results = search_services(self.conn, search_term)
            columns = ['id', 'title', 'type', 'description', 'provider_name']
            self.display_results(results, columns, f"Search Results: {search_term}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def add_service_action(self):
        """Add a service."""
        try:
            title = self.add_service_title.get().strip()
            if not title:
                messagebox.showwarning("Warning", "Title is required.")
                return
            
            service_type = self.add_service_type.get().strip().upper()
            description = self.add_service_desc.get().strip()
            description = description if description else None
            
            service_id = add_service(self.conn, self.current_user_id, title, service_type, description)
            messagebox.showinfo("Success", f"Service created successfully!\nService ID: {service_id}")
            
            self.add_service_title.delete(0, tk.END)
            self.add_service_type.delete(0, tk.END)
            self.add_service_desc.delete(0, tk.END)
            self.show_my_services()
        except ValueError:
            messagebox.showerror("Error", "Please check your inputs.")
            self.conn.rollback()
        except psycopg2.IntegrityError as e:
            messagebox.showerror("Error", f"Error: {e}")
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.conn.rollback()
    
    def show_proximity_view(self):
        """Display proximity view."""
        try:
            from main import view_proximity
            distance = self.prox_distance.get().strip()
            max_distance = float(distance) if distance else 1.0
            
            results = view_proximity(self.conn, self.current_user_id, max_distance)
            
            if not results:
                messagebox.showinfo("No Results", "No individuals found in this radius.")
                return
            
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
            self.display_results(formatted_results, columns, f"Nearby People ({max_distance} km)")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid distance.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def create_connections_tab(self):
        """Create the connections tab."""
        conn_frame = ttk.Frame(self.notebook)
        self.notebook.add(conn_frame, text="Connections")
        
        # My Connections section
        my_conn_frame = ttk.LabelFrame(conn_frame, text="My Connections", padding=10)
        my_conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            my_conn_frame,
            text="View My Connections",
            command=self.show_my_connections,
            bg='#4CAF50',
            fg='white',
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        # My Communities Collaborations section
        my_comm_collab_frame = ttk.LabelFrame(conn_frame, text="My Communities' Collaborations", padding=10)
        my_comm_collab_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(my_comm_collab_frame, text="Community ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.view_my_comm_collab_id = tk.Entry(my_comm_collab_frame, width=20)
        self.view_my_comm_collab_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            my_comm_collab_frame,
            text="View Collaborations",
            command=self.show_my_community_collaborations,
            bg='#2196F3',
            fg='white',
            width=25
        ).grid(row=0, column=2, padx=5, pady=5)
    
    def create_exclusion_tab(self):
        """Create the exclusion votes tab."""
        excl_frame = ttk.Frame(self.notebook)
        self.notebook.add(excl_frame, text="Exclusion Votes")
        
        # View my communities members section
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
            width=25
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Cast vote section
        vote_frame = ttk.LabelFrame(excl_frame, text="Cast Exclusion Vote", padding=10)
        vote_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(vote_frame, text="Membership ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.vote_membership_id = tk.Entry(vote_frame, width=20)
        self.vote_membership_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(vote_frame, text="Vote (Exclude?):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.vote_choice = tk.BooleanVar()
        tk.Checkbutton(vote_frame, text="Yes, exclude", variable=self.vote_choice).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        tk.Button(
            vote_frame,
            text="Cast Vote",
            command=self.cast_vote_action,
            bg='#f44336',
            fg='white',
            width=25
        ).grid(row=1, column=2, padx=5, pady=5)
        
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
            width=25
        ).grid(row=0, column=2, padx=5, pady=5)
        
        tk.Button(
            view_votes_frame,
            text="View Vote Statistics",
            command=self.show_vote_stats,
            bg='#9C27B0',
            fg='white',
            width=25
        ).grid(row=0, column=3, padx=5, pady=5)
    
    def show_my_connections(self):
        """Display user's connections."""
        try:
            results = view_individual_connections(self.conn, self.current_user_id)
            
            if not results:
                messagebox.showinfo("No Results", "You have no connections yet.")
                return
            
            columns = ['connected_individual_id', 'connected_name', 'connected_email', 'latitude', 'longitude']
            self.display_results(results, columns, "My Connections")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def show_my_community_collaborations(self):
        """Display collaborations for a community."""
        try:
            community_id = int(self.view_my_comm_collab_id.get())
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
            membership_id = int(self.vote_membership_id.get())
            vote = self.vote_choice.get()
            
            vote_id = cast_exclusion_vote(self.conn, self.current_user_id, membership_id, vote)
            vote_text = "for exclusion" if vote else "against exclusion"
            messagebox.showinfo("Success", f"Vote cast successfully!\nVote ID: {vote_id}\nVoted {vote_text}")
            
            # Update the view votes field with the membership_id used
            self.view_votes_membership_id.delete(0, tk.END)
            self.view_votes_membership_id.insert(0, str(membership_id))
            
            # Clear vote form
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
    
    def logout(self):
        """Handle user logout."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.current_user_id = None
            self.current_user_info = None
            self.create_login_screen()
    
    def on_closing(self):
        """Handle window closing."""
        if self.conn:
            self.conn.close()
        self.root.destroy()


def main():
    """Main function to run the user interface."""
    root = tk.Tk()
    app = UserInterface(root)
    root.mainloop()


if __name__ == "__main__":
    main()

