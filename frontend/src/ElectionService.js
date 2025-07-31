// Service to handle election data and API calls
class ElectionService {
  constructor() {
    this.baseUrl = 'http://localhost:8000'; // Backend API URL
  }

  // Fetch election results from backend
  async getElectionResults() {
    try {
      const response = await fetch(`${this.baseUrl}/election-results`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching election results:', error);
      // Return mock data for development
      return this.getMockElectionData();
    }
  }

  // Mock election data for development/testing
  getMockElectionData() {
    return {
      states: {
        'CA': { winner: 'Democrat', votes: { Democrat: 11110250, Republican: 6006429 }, electoral_votes: 54 },
        'TX': { winner: 'Republican', votes: { Democrat: 5259126, Republican: 5890347 }, electoral_votes: 40 },
        'FL': { winner: 'Republican', votes: { Democrat: 5297045, Republican: 5668731 }, electoral_votes: 30 },
        'NY': { winner: 'Democrat', votes: { Democrat: 5244886, Republican: 3244798 }, electoral_votes: 28 },
        'PA': { winner: 'Republican', votes: { Democrat: 3458229, Republican: 3377674 }, electoral_votes: 19 },
        'IL': { winner: 'Democrat', votes: { Democrat: 3471133, Republican: 2446891 }, electoral_votes: 19 },
        'OH': { winner: 'Republican', votes: { Democrat: 2940044, Republican: 3154834 }, electoral_votes: 17 },
        'GA': { winner: 'Republican', votes: { Democrat: 2473633, Republican: 2661405 }, electoral_votes: 16 },
        'NC': { winner: 'Republican', votes: { Democrat: 2684292, Republican: 2758775 }, electoral_votes: 16 },
        'MI': { winner: 'Republican', votes: { Democrat: 2804040, Republican: 2649852 }, electoral_votes: 15 }
      },
      summary: {
        total_electoral_votes: 538,
        democrat_electoral: 226,
        republican_electoral: 312,
        winner: 'Republican'
      },
      last_updated: new Date().toISOString()
    };
  }

  // Get color for state based on election results
  getStateColor(stateCode, electionData) {
    if (!electionData || !electionData.states || !electionData.states[stateCode]) {
      return '#e0e0e0'; // Default gray for no data
    }

    const stateResult = electionData.states[stateCode];
    switch (stateResult.winner) {
      case 'Democrat':
        return '#2196F3'; // Blue
      case 'Republican':
        return '#F44336'; // Red
      case 'Independent':
        return '#9C27B0'; // Purple
      default:
        return '#e0e0e0'; // Gray
    }
  }

  // Calculate vote margin percentage
  getVoteMargin(stateCode, electionData) {
    if (!electionData || !electionData.states || !electionData.states[stateCode]) {
      return 0;
    }

    const stateResult = electionData.states[stateCode];
    const votes = stateResult.votes;
    const totalVotes = Object.values(votes).reduce((sum, count) => sum + count, 0);
    
    if (totalVotes === 0) return 0;

    const sortedVotes = Object.entries(votes).sort((a, b) => b[1] - a[1]);
    const margin = ((sortedVotes[0][1] - sortedVotes[1][1]) / totalVotes) * 100;
    
    return Math.round(margin * 100) / 100; // Round to 2 decimal places
  }

  // Format vote counts for display
  formatVoteCount(count) {
    if (count >= 1000000) {
      return (count / 1000000).toFixed(1) + 'M';
    } else if (count >= 1000) {
      return (count / 1000).toFixed(0) + 'K';
    }
    return count.toString();
  }
}

export default new ElectionService();
