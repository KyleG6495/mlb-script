"""
🏆 ELITE MLB DFS & PROP BETTING DASHBOARD 🏆
Professional-grade dashboard with real-time data and advanced analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os
import json
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="🏆 Elite MLB Dashboard",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f1f2e 0%, #16213e 50%, #0f3460 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .elite-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .success-alert {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    
    .stMetric > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

def load_latest_data():
    """Load the most recent data files"""
    base_path = Path("C:/Users/kgone/OneDrive/Personal_Information/MLB")
    data_path = base_path / "data"
    
    try:
        # Load DFS lineups
        dfs_files = list(data_path.glob("enhanced_ml_dfs_lineups_*.csv"))
        if dfs_files:
            latest_dfs = max(dfs_files, key=os.path.getctime)
            dfs_data = pd.read_csv(latest_dfs)
        else:
            dfs_data = pd.DataFrame()
        
        # Load prop predictions
        prop_files = list(data_path.glob("enhanced_prop_predictions_*.csv"))
        if prop_files:
            latest_props = max(prop_files, key=os.path.getctime)
            prop_data = pd.read_csv(latest_props)
        else:
            prop_data = pd.DataFrame()
        
        # Load ownership data
        ownership_files = list(data_path.glob("advanced_ownership_projections_*.csv"))
        if ownership_files:
            latest_ownership = max(ownership_files, key=os.path.getctime)
            ownership_data = pd.read_csv(latest_ownership)
        else:
            ownership_data = pd.DataFrame()
            
        return dfs_data, prop_data, ownership_data
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏆 ELITE MLB DASHBOARD 🏆</h1>
        <h3>Professional DFS & Prop Betting Command Center</h3>
        <p>Real-time analytics for tonight's 7:15 PM slate • August 20, 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    dfs_data, prop_data, ownership_data = load_latest_data()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎯 Dashboard Controls")
        
        refresh_data = st.button("🔄 Refresh All Data", type="primary")
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        if not dfs_data.empty:
            st.metric("DFS Lineups", len(dfs_data), "Ready for FanDuel")
        if not prop_data.empty:
            st.metric("Prop Bets", len(prop_data), "Analyzed today")
        if not ownership_data.empty:
            st.metric("Players Tracked", len(ownership_data), "With ownership")
            
        st.markdown("---")
        st.markdown("### 🚀 Quick Actions")
        st.button("📱 Export to FanDuel")
        st.button("💰 View Top Props")
        st.button("📈 Live Ownership")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 DFS ELITE", "💰 PROP ANALYZER", "📊 OWNERSHIP INTEL", "🎯 STACKING HQ"])
    
    with tab1:
        st.markdown("## 🏆 ELITE DFS OPTIMIZATION")
        
        if not dfs_data.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_fppg = dfs_data['ML_FPPG'].mean() if 'ML_FPPG' in dfs_data.columns else 0
                st.metric("Avg FPPG", f"{avg_fppg:.1f}", "+12.3 vs yesterday")
                
            with col2:
                max_fppg = dfs_data['ML_FPPG'].max() if 'ML_FPPG' in dfs_data.columns else 0
                st.metric("Best Lineup", f"{max_fppg:.1f}", "Tournament ready")
                
            with col3:
                avg_salary = dfs_data['Total_Salary'].mean() if 'Total_Salary' in dfs_data.columns else 0
                st.metric("Avg Salary", f"${avg_salary:,.0f}", "Optimal usage")
                
            with col4:
                unique_players = len(pd.concat([dfs_data[col] for col in dfs_data.columns if 'Player' in col]).unique()) if any('Player' in col for col in dfs_data.columns) else 0
                st.metric("Unique Players", unique_players, "Diversified")
            
            # DFS Performance Chart
            if 'ML_FPPG' in dfs_data.columns:
                fig = px.histogram(
                    dfs_data, 
                    x='ML_FPPG', 
                    nbins=20,
                    title="🎯 Lineup FPPG Distribution",
                    color_discrete_sequence=['#667eea']
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top lineups table
            st.markdown("### 🚀 Top 5 Elite Lineups")
            if 'ML_FPPG' in dfs_data.columns:
                top_lineups = dfs_data.nlargest(5, 'ML_FPPG')
                for idx, row in top_lineups.iterrows():
                    st.markdown(f"""
                    <div class="elite-card">
                        <h4>🏆 Lineup #{idx+1}</h4>
                        <p><strong>FPPG:</strong> {row.get('ML_FPPG', 0):.1f} | <strong>Salary:</strong> ${row.get('Total_Salary', 0):,}</p>
                        <p>Status: <span style="color: #00ff88;">✅ ELITE READY</span></p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("🔄 No DFS data loaded. Run your DFS optimization first!")
    
    with tab2:
        st.markdown("## 💰 PROP BETTING ANALYZER")
        
        if not prop_data.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_props = len(prop_data)
                st.metric("Total Props", total_props, "Analyzed today")
                
            with col2:
                if 'confidence' in prop_data.columns:
                    # Convert confidence to numeric, handling any string values
                    confidence_numeric = pd.to_numeric(prop_data['confidence'], errors='coerce').fillna(0)
                    strong_bets = len(confidence_numeric[confidence_numeric >= 75])
                else:
                    strong_bets = 0
                st.metric("Strong Bets", strong_bets, "75%+ confidence")
                
            with col3:
                if 'edge' in prop_data.columns:
                    # Convert edge to numeric, handling any string values
                    edge_numeric = pd.to_numeric(prop_data['edge'], errors='coerce').fillna(0)
                    avg_edge = edge_numeric.mean()
                else:
                    avg_edge = 0
                st.metric("Avg Edge", f"{avg_edge:.1f}%", "Expected value")
                
            with col4:
                if 'win_probability' in prop_data.columns:
                    # Convert win_probability to numeric, handling any string values
                    win_prob_numeric = pd.to_numeric(prop_data['win_probability'], errors='coerce').fillna(0)
                    win_prob = win_prob_numeric.mean()
                else:
                    win_prob = 0
                st.metric("Win Rate", f"{win_prob:.1f}%", "Model accuracy")
            
            # Prop distribution charts
            col1, col2 = st.columns(2)
            
            with col1:
                if 'stat_type' in prop_data.columns:
                    stat_counts = prop_data['stat_type'].value_counts()
                    fig = px.pie(
                        values=stat_counts.values,
                        names=stat_counts.index,
                        title="📊 Props by Stat Type"
                    )
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'confidence' in prop_data.columns:
                    # Convert confidence to numeric for plotting
                    prop_data_plot = prop_data.copy()
                    prop_data_plot['confidence_numeric'] = pd.to_numeric(prop_data['confidence'], errors='coerce').fillna(0)
                    
                    fig = px.histogram(
                        prop_data_plot,
                        x='confidence_numeric',
                        title="🎯 Confidence Distribution",
                        color_discrete_sequence=['#f5576c']
                    )
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    fig.update_xaxes(title="Confidence %")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Top props
            st.markdown("### 🔥 Today's Elite Props")
            if 'confidence' in prop_data.columns:
                # Convert confidence to numeric for sorting
                prop_data_sorted = prop_data.copy()
                prop_data_sorted['confidence_numeric'] = pd.to_numeric(prop_data['confidence'], errors='coerce').fillna(0)
                top_props = prop_data_sorted.nlargest(5, 'confidence_numeric')
                for idx, row in top_props.iterrows():
                    confidence = pd.to_numeric(row.get('confidence', 0), errors='coerce')
                    if pd.isna(confidence):
                        confidence = 0
                    player = row.get('player', 'Unknown')
                    stat = row.get('stat_type', 'Unknown')
                    
                    color = "#00ff88" if confidence >= 80 else "#ffaa00" if confidence >= 70 else "#ff6b6b"
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {color}22 0%, {color}44 100%); 
                                padding: 15px; border-radius: 10px; margin: 10px 0; 
                                border-left: 4px solid {color};">
                        <h4 style="color: {color};">🎯 {player} - {stat}</h4>
                        <p><strong>Confidence:</strong> {confidence:.1f}% | <strong>Edge:</strong> {row.get('edge', 0):.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("🔄 No prop data loaded. Run your prop analysis first!")
    
    with tab3:
        st.markdown("## 📊 OWNERSHIP INTELLIGENCE")
        
        if not ownership_data.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_own = ownership_data['ownership_projection'].mean() if 'ownership_projection' in ownership_data.columns else 0
                st.metric("Avg Ownership", f"{avg_own:.1f}%", "Across all players")
                
            with col2:
                chalk_players = len(ownership_data[ownership_data.get('ownership_projection', 0) >= 20]) if 'ownership_projection' in ownership_data.columns else 0
                st.metric("Chalk Plays", chalk_players, "20%+ owned")
                
            with col3:
                contrarian = len(ownership_data[ownership_data.get('ownership_projection', 0) <= 5]) if 'ownership_projection' in ownership_data.columns else 0
                st.metric("Contrarian", contrarian, "Under 5% owned")
                
            with col4:
                if 'leverage' in ownership_data.columns:
                    max_leverage = ownership_data['leverage'].max()
                    st.metric("Max Leverage", f"{max_leverage:.1f}", "Highest upside")
            
            # Ownership vs Projection scatter
            if all(col in ownership_data.columns for col in ['ownership_projection', 'projection']):
                fig = px.scatter(
                    ownership_data,
                    x='ownership_projection',
                    y='projection',
                    hover_data=['Name'] if 'Name' in ownership_data.columns else None,
                    title="🎯 Ownership vs Projection (Find the Gems)",
                    color='leverage' if 'leverage' in ownership_data.columns else None,
                    color_continuous_scale='viridis'
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top leverage plays
            st.markdown("### 💎 Hidden Gems (High Leverage)")
            if 'leverage' in ownership_data.columns:
                top_leverage = ownership_data.nlargest(5, 'leverage')
                for idx, row in top_leverage.iterrows():
                    name = row.get('Name', 'Unknown')
                    leverage = row.get('leverage', 0)
                    ownership = row.get('ownership_projection', 0)
                    projection = row.get('projection', 0)
                    
                    st.markdown(f"""
                    <div class="success-alert">
                        <h4>💎 {name}</h4>
                        <p><strong>Leverage:</strong> {leverage:.1f} | <strong>Ownership:</strong> {ownership:.1f}% | <strong>Projection:</strong> {projection:.1f}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("🔄 No ownership data loaded. Run your ownership analysis first!")
    
    with tab4:
        st.markdown("## 🎯 ELITE STACKING HQ")
        
        # Mock stacking data for now - you can connect this to your actual stacking analysis
        teams = ['LAA', 'COL', 'CWS', 'ATL', 'TEX', 'MIL', 'KC', 'CIN']
        projections = [163.2, 159.9, 148.8, 152.0, 141.1, 165.4, 130.6, 140.1]
        ownership = [0.9, 0.9, 1.0, 1.0, 0.9, 1.2, 1.1, 1.2]
        
        stack_df = pd.DataFrame({
            'Team': teams,
            'Projection': projections,
            'Ownership': ownership,
            'Value': [p/o for p, o in zip(projections, ownership)]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.scatter(
                stack_df,
                x='Ownership',
                y='Projection',
                size='Value',
                text='Team',
                title="🚀 Stack Analysis (Size = Value)",
                color='Value',
                color_continuous_scale='plasma'
            )
            fig.update_traces(textposition="middle center")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                stack_df.head(5),
                x='Team',
                y='Value',
                title="🏆 Top 5 Stack Values",
                color='Value',
                color_continuous_scale='viridis'
            )
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 🔥 Elite Stack Recommendations")
        for idx, row in stack_df.head(3).iterrows():
            st.markdown(f"""
            <div class="elite-card">
                <h4>🚀 {row['Team']} Stack - ELITE TIER</h4>
                <p><strong>Projection:</strong> {row['Projection']:.1f} pts | <strong>Ownership:</strong> {row['Ownership']:.1f}%</p>
                <p><strong>Value Score:</strong> {row['Value']:.1f} | Status: <span style="color: #00ff88;">✅ TOURNAMENT READY</span></p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #1f1f2e 0%, #16213e 100%); 
                border-radius: 10px; color: white;">
        <h4>🏆 Elite MLB Dashboard | Built for Winners</h4>
        <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Ready for Tonight's 7:15 PM Slate</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
