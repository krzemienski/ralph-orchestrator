#!/usr/bin/env ruby
# Script to add Phase 8 SwiftUI files (Library, Host, Settings) to RalphMobile Xcode project

require 'xcodeproj'

project_path = '/Users/nick/Desktop/ralph-orchestrator/ios/RalphMobile.xcodeproj'
project = Xcodeproj::Project.open(project_path)

# Get the main target
target = project.targets.find { |t| t.name == 'RalphMobile' }

# Get the RalphMobile group
ralph_mobile_group = project.main_group['RalphMobile']
views_group = ralph_mobile_group['Views']

# Remove existing groups if they exist to avoid duplicates
['Library', 'Host', 'Settings'].each do |name|
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

# Create Library subgroup
library_group = views_group.new_group('Library', 'Library')
puts "Created Library group"

# Create Host subgroup
host_group = views_group.new_group('Host', 'Host')
puts "Created Host group"

# Create Settings subgroup
settings_group = views_group.new_group('Settings', 'Settings')
puts "Created Settings group"

# Files to add - Library group
library_files = ['LibraryView.swift']
library_files.each do |file_name|
  file_ref = library_group.new_file(file_name)
  target.source_build_phase.add_file_reference(file_ref)
  puts "Added #{file_name} to Library group"
end

# Files to add - Host group
host_files = ['HostMetricsView.swift']
host_files.each do |file_name|
  file_ref = host_group.new_file(file_name)
  target.source_build_phase.add_file_reference(file_ref)
  puts "Added #{file_name} to Host group"
end

# Files to add - Settings group
settings_files = ['SettingsView.swift']
settings_files.each do |file_name|
  file_ref = settings_group.new_file(file_name)
  target.source_build_phase.add_file_reference(file_ref)
  puts "Added #{file_name} to Settings group"
end

# Save the project
project.save
puts "Project saved successfully"
