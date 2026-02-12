#!/usr/bin/env ruby
# Script to add V5 SwiftUI files to RalphMobile Xcode project

require 'xcodeproj'

project_path = '/Users/nick/Desktop/ralph-orchestrator/ios/RalphMobile.xcodeproj'
project = Xcodeproj::Project.open(project_path)

# Get the main target
target = project.targets.find { |t| t.name == 'RalphMobile' }

# Get the RalphMobile group
ralph_mobile_group = project.main_group['RalphMobile']
views_group = ralph_mobile_group['Views']

# Remove existing broken groups if they exist
['Navigation', 'Ralph', 'Create'].each do |name|
  existing = views_group[name]
  if existing
    # Remove all file references from build phase
    existing.files.each do |file|
      target.source_build_phase.files.delete_if { |bf| bf.file_ref == file }
    end
    existing.remove_from_project
    puts "Removed existing #{name} group"
  end
end

# Create Navigation subgroup
navigation_group = views_group.new_group('Navigation', 'Navigation')
puts "Created Navigation group"

# Create Ralph subgroup
ralph_group = views_group.new_group('Ralph', 'Ralph')
puts "Created Ralph group"

# Create Create subgroup
create_group = views_group.new_group('Create', 'Create')
puts "Created Create group"

# Files to add - Navigation group
navigation_files = [
  'MainNavigationView.swift',
  'SidebarView.swift'
]

navigation_files.each do |file_name|
  # Use just the filename since the group path is already set
  file_ref = navigation_group.new_file(file_name)
  target.source_build_phase.add_file_reference(file_ref)
  puts "Added #{file_name} to Navigation group"
end

# Files to add - Ralph group
ralph_files = [
  'UnifiedRalphView.swift',
  'HatFlowView.swift',
  'SignalEmitterView.swift',
  'ScratchpadContentView.swift'
]

ralph_files.each do |file_name|
  file_ref = ralph_group.new_file(file_name)
  target.source_build_phase.add_file_reference(file_ref)
  puts "Added #{file_name} to Ralph group"
end

# Files to add - Create group
create_files = [
  'CreateRalphWizard.swift'
]

create_files.each do |file_name|
  file_ref = create_group.new_file(file_name)
  target.source_build_phase.add_file_reference(file_ref)
  puts "Added #{file_name} to Create group"
end

# Save the project
project.save
puts "Project saved successfully"
