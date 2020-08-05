MEMORY
     {
        OCRAM (wx) : ORIGIN = 0x20200000, LENGTH = 262144
        DTCM (wx) : ORIGIN = 0x20000000, LENGTH = 131072
        ITCM (wx) : ORIGIN = 0x0, LENGTH = 131072
     }
 OUTPUT_FORMAT("elf32-littlearm")
_region_min_align = 4;
MEMORY
    {
    FLASH (rx) : ORIGIN = (0x60000000 + 0x0), LENGTH = (8192*1K - 0x0)
    SRAM (wx) : ORIGIN = 0x80000000, LENGTH = (32768 * 1K - 16 * 1K)
    IDT_LIST (wx) : ORIGIN = (0x80000000 + (32768 * 1K - 16 * 1K)), LENGTH = 2K
    }
ENTRY("__start")
SECTIONS
    {
 .rel.plt :
 {
 *(.rel.plt)
 PROVIDE_HIDDEN (__rel_iplt_start = .);
 *(.rel.iplt)
 PROVIDE_HIDDEN (__rel_iplt_end = .);
 }
 .rela.plt :
 {
 *(.rela.plt)
 PROVIDE_HIDDEN (__rela_iplt_start = .);
 *(.rela.iplt)
 PROVIDE_HIDDEN (__rela_iplt_end = .);
 }
 .rel.dyn :
 {
 *(.rel.*)
 }
 .rela.dyn :
 {
 *(.rela.*)
 }
    /DISCARD/ :
 {
 *(.plt)
 }
    /DISCARD/ :
 {
 *(.iplt)
 }
   
 _image_rom_start = (0x60000000 + 0x0);
    rom_start :
 {
. = 0x0;
. = ALIGN(4);
_vector_start = .;
KEEP(*(.exc_vector_table))
KEEP(*(".exc_vector_table.*"))
KEEP(*(.gnu.linkonce.irq_vector_table))
KEEP(*(.vectors))
_vector_end = .;
KEEP(*(.openocd_dbg))
KEEP(*(".openocd_dbg.*"))
 } > SRAM
    text :
 {
 _image_text_start = .;
 *(.text)
 *(".text.*")
 *(.gnu.linkonce.t.*)
 *(.glue_7t) *(.glue_7) *(.vfp11_veneer) *(.v4_bx)
 } > SRAM
 _image_text_end = .;
 .ARM.extab :
 {
 *(.ARM.extab* .gnu.linkonce.armextab.*)
 } > SRAM
 .ARM.exidx :
 {
 __exidx_start = .;
 *(.ARM.exidx* gnu.linkonce.armexidx.*)
 __exidx_end = .;
 } > SRAM
 _image_rodata_start = .;
 sw_isr_table :
 {
  . = ALIGN(0);
  *(.gnu.linkonce.sw_isr_table)
 } > SRAM
 ctors :
 {
  . = ALIGN(4);
  __CTOR_LIST__ = .;
  LONG((__CTOR_END__ - __CTOR_LIST__) / 4 - 2)
  KEEP(*(SORT(".ctors*")))
  LONG(0)
  __CTOR_END__ = .;
 } > SRAM
 init_array :
 {
  . = ALIGN(4);
  __init_array_start = .;
  KEEP(*(SORT(".init_array*")))
  __init_array_end = .;
 } > SRAM
 app_shmem_regions :
 {
  __app_shmem_regions_start = .;
  KEEP(*(SORT(".app_regions.*")));
  __app_shmem_regions_end = .;
 } > SRAM
 devconfig :
 {
  __devconfig_start = .;
  *(".devconfig.*")
  KEEP(*(SORT(".devconfig*")))
  __devconfig_end = .;
 } > SRAM
 net_l2 :
 {
  __net_l2_start = .;
  *(".net_l2.init")
  KEEP(*(SORT(".net_l2.init*")))
  __net_l2_end = .;
 } > SRAM
 _bt_channels_area : SUBALIGN(4)
 {
  _bt_l2cap_fixed_chan_list_start = .;
  KEEP(*(SORT("._bt_l2cap_fixed_chan.static.*")))
  _bt_l2cap_fixed_chan_list_end = .;
 } > SRAM
 _bt_services_area : SUBALIGN(4)
 {
  _bt_gatt_service_static_list_start = .;
  KEEP(*(SORT("._bt_gatt_service_static.static.*")))
  _bt_gatt_service_static_list_end = .;
 } > SRAM
 log_const_sections :
 {
  __log_const_start = .;
  KEEP(*(SORT(.log_const_*)));
  __log_const_end = .;
 } > SRAM
 log_backends_sections :
 {
  __log_backends_start = .;
  KEEP(*("._log_backend.*"));
  __log_backends_end = .;
 } > SRAM
 shell_root_cmds_sections :
 {
  __shell_root_cmds_start = .;
  KEEP(*(SORT(.shell_root_cmd_*)));
  __shell_root_cmds_end = .;
 } > SRAM
 font_entry_sections :
 {
  __font_entry_start = .;
  KEEP(*(SORT("._cfb_font.*")))
  __font_entry_end = .;
 } > SRAM
 tracing_backends_sections :
 {
  _tracing_backend_list_start = .;
  KEEP(*("._tracing_backend.*"));
  _tracing_backend_list_end = .;
 } > SRAM
    rodata :
 {
 *(.rodata)
 *(".rodata.*")
 *(.gnu.linkonce.r.*)
 . = ALIGN(4);
 } > SRAM
 .gcc_except_table : ONLY_IF_RO
 {
 *(.gcc_except_table .gcc_except_table.*)
 } > SRAM


    .got :
    {
        . = ALIGN(4);
        *(.got.plt)
        *(.igot.plt)
        *(.got*)
        *(.igot)
    } > SRAM

	.swift5 :
	{
        . = ALIGN(4);
        __start_swift5_typeref = .;
        *(swift5_typeref*)
        __stop_swift5_typeref = .;

        . = ALIGN(4);
        __start_swift5_reflstr = .;
        *(swift5_reflstr)
        __stop_swift5_reflstr = .;

        . = ALIGN(4);
        __start_swift5_fieldmd = .;
        *(swift5_fieldmd)
        __stop_swift5_fieldmd = .;

        . = ALIGN(4);
        __start_swift5_assocty = .;
        *(swift5_assocty)
        __stop_swift5_assocty = .;

        . = ALIGN(4);
        __start_swift5_replace = .;
        *(swift5_replace)
        __stop_swift5_replace = .;

        . = ALIGN(4);
        __start_swift5_capture = .;
        *(swift5_capture)
        __stop_swift5_capture = .;

        . = ALIGN(4);
        __start_swift5_builtin = .;
        *(swift5_builtin)
        __stop_swift5_builtin = .;

        . = ALIGN(4);
        __start_swift5_type_metadata = .;
        *(swift5_type_metadata*)
        __stop_swift5_type_metadata = .;

        . = ALIGN(4);
        __start_swift5_protocols = .;
        *(swift5_protocols*)
        __stop_swift5_protocols = .;

        . = ALIGN(4);
        __start_swift5_protocol_conformances = .;
        *(swift5_protocol_conformances*)
        __stop_swift5_protocol_conformances = .;

        . = ALIGN(4);
    } > SRAM


 _image_rodata_end = .;
 . = ALIGN(_region_min_align);
 _image_rom_end = .;
   
 . = 0x80000000;
 . = ALIGN(_region_min_align);
 _image_ram_start = .;
.ramfunc :
{
 . = ALIGN(_region_min_align);
 _ramfunc_ram_start = .;
 *(.ramfunc)
 *(".ramfunc.*")
 . = ALIGN(_region_min_align);
 _ramfunc_ram_end = .;
} > SRAM
_ramfunc_ram_size = _ramfunc_ram_end - _ramfunc_ram_start;
_ramfunc_rom_start = LOADADDR(.ramfunc);
    bss (NOLOAD) :
 {
        . = ALIGN(4);
 __bss_start = .;
 __kernel_ram_start = .;
 *(.bss)
 *(".bss.*")
 *(COMMON)
 *(".kernel_bss.*")
 __bss_end = ALIGN(4);
 } > SRAM
    noinit (NOLOAD) :
        {
        *(.noinit)
        *(".noinit.*")
 *(".kernel_noinit.*")
        } > SRAM
    datas :
 {
 __data_ram_start = .;
 *(.data)
 *(".data.*")
 *(".kernel.*")
 } > SRAM
    __data_rom_start = LOADADDR(datas);
 initlevel :
 {
  __device_init_start = .; __device_PRE_KERNEL_1_start = .; KEEP(*(SORT(.init_PRE_KERNEL_1[0-9]))); KEEP(*(SORT(.init_PRE_KERNEL_1[1-9][0-9]))); __device_PRE_KERNEL_2_start = .; KEEP(*(SORT(.init_PRE_KERNEL_2[0-9]))); KEEP(*(SORT(.init_PRE_KERNEL_2[1-9][0-9]))); __device_POST_KERNEL_start = .; KEEP(*(SORT(.init_POST_KERNEL[0-9]))); KEEP(*(SORT(.init_POST_KERNEL[1-9][0-9]))); __device_APPLICATION_start = .; KEEP(*(SORT(.init_APPLICATION[0-9]))); KEEP(*(SORT(.init_APPLICATION[1-9][0-9]))); __device_init_end = .;
 } > SRAM
 initlevel_error :
 {
  KEEP(*(SORT(.init_[_A-Z0-9]*)))
 }
 ASSERT(SIZEOF(initlevel_error) == 0, "Undefined initialization levels used.")
 initshell :
 {
  __shell_module_start = .; KEEP(*(".shell_module_*")); __shell_module_end = .; __shell_cmd_start = .; KEEP(*(".shell_cmd_*")); __shell_cmd_end = .;
 } > SRAM
 log_dynamic_sections :
 {
  __log_dynamic_start = .;
  KEEP(*(SORT(.log_dynamic_*)));
  __log_dynamic_end = .;
 } > SRAM
 _static_thread_area : SUBALIGN(4)
 {
  __static_thread_data_list_start = .;
  KEEP(*(SORT(".__static_thread_data.static.*")))
  __static_thread_data_list_end = .;
 } > SRAM
 _k_timer_area : SUBALIGN(4)
 {
  _k_timer_list_start = .;
  KEEP(*("._k_timer.static.*"))
  _k_timer_list_end = .;
 } > SRAM
 _k_mem_slab_area : SUBALIGN(4)
 {
  _k_mem_slab_list_start = .;
  KEEP(*("._k_mem_slab.static.*"))
  _k_mem_slab_list_end = .;
 } > SRAM
 _k_mem_pool_area : SUBALIGN(4)
 {
  _k_mem_pool_list_start = .;
  KEEP(*("._k_mem_pool.static.*"))
  _k_mem_pool_list_end = .;
 } > SRAM
 _k_sem_area : SUBALIGN(4)
 {
  _k_sem_list_start = .;
  KEEP(*("._k_sem.static.*"))
  KEEP(*("._sys_sem.static.*"))
  _k_sem_list_end = .;
 } > SRAM
 _k_mutex_area : SUBALIGN(4)
 {
  _k_mutex_list_start = .;
  KEEP(*("._k_mutex.static.*"))
  _k_mutex_list_end = .;
 } > SRAM
 _k_queue_area : SUBALIGN(4)
 {
  _k_queue_list_start = .;
  KEEP(*("._k_queue.static.*"))
  KEEP(*("._k_fifo.static.*"))
  KEEP(*("._k_lifo.static.*"))
  _k_queue_list_end = .;
 } > SRAM
 _k_stack_area : SUBALIGN(4)
 {
  _k_stack_list_start = .;
  KEEP(*("._k_stack.static.*"))
  _k_stack_list_end = .;
 } > SRAM
 _k_msgq_area : SUBALIGN(4)
 {
  _k_msgq_list_start = .;
  KEEP(*("._k_msgq.static.*"))
  _k_msgq_list_end = .;
 } > SRAM
 _k_mbox_area : SUBALIGN(4)
 {
  _k_mbox_list_start = .;
  KEEP(*("._k_mbox.static.*"))
  _k_mbox_list_end = .;
 } > SRAM
 _k_pipe_area : SUBALIGN(4)
 {
  _k_pipe_list_start = .;
  KEEP(*("._k_pipe.static.*"))
  _k_pipe_list_end = .;
 } > SRAM
 _net_buf_pool_area : SUBALIGN(4)
 {
  _net_buf_pool_list = .;
  KEEP(*(SORT("._net_buf_pool.static.*")))
 } > SRAM
 net_if : SUBALIGN(4)
 {
  __net_if_start = .;
  *(".net_if.*")
  KEEP(*(SORT(".net_if.*")))
  __net_if_end = .;
 } > SRAM
 net_if_dev : SUBALIGN(4)
 {
  __net_if_dev_start = .;
  *(".net_if_dev.*")
  KEEP(*(SORT(".net_if_dev.*")))
  __net_if_dev_end = .;
 } > SRAM
 net_l2_data : SUBALIGN(4)
 {
  __net_l2_data_start = .;
  *(".net_l2.data")
  KEEP(*(SORT(".net_l2.data*")))
  __net_l2_data_end = .;
 } > SRAM
     priv_stacks_noinit :
        {
        z_priv_stacks_ram_start = .;
        *(".priv_stacks.noinit")
        z_priv_stacks_ram_end = .;
        } > SRAM
 .gcc_except_table : ONLY_IF_RW
 {
 *(.gcc_except_table .gcc_except_table.*)
 } > SRAM
    __data_ram_end = .;
    _image_ram_end = .;
    _end = .;
    __kernel_ram_end = 0x80000000 + (32768 * 1K - 16 * 1K);
    __kernel_ram_size = __kernel_ram_end - __kernel_ram_start;
   
/DISCARD/ :
{
 KEEP(*(.irq_info))
 KEEP(*(.intList))
}
 .stab 0 : { *(.stab) }
 .stabstr 0 : { *(.stabstr) }
 .stab.excl 0 : { *(.stab.excl) }
 .stab.exclstr 0 : { *(.stab.exclstr) }
 .stab.index 0 : { *(.stab.index) }
 .stab.indexstr 0 : { *(.stab.indexstr) }
 .gnu.build.attributes 0 : { *(.gnu.build.attributes .gnu.build.attributes.*) }
 .comment 0 : { *(.comment) }
 .debug 0 : { *(.debug) }
 .line 0 : { *(.line) }
 .debug_srcinfo 0 : { *(.debug_srcinfo) }
 .debug_sfnames 0 : { *(.debug_sfnames) }
 .debug_aranges 0 : { *(.debug_aranges) }
 .debug_pubnames 0 : { *(.debug_pubnames) }
 .debug_info 0 : { *(.debug_info .gnu.linkonce.wi.*) }
 .debug_abbrev 0 : { *(.debug_abbrev) }
 .debug_line 0 : { *(.debug_line .debug_line.* .debug_line_end ) }
 .debug_frame 0 : { *(.debug_frame) }
 .debug_str 0 : { *(.debug_str) }
 .debug_loc 0 : { *(.debug_loc) }
 .debug_macinfo 0 : { *(.debug_macinfo) }
 .debug_weaknames 0 : { *(.debug_weaknames) }
 .debug_funcnames 0 : { *(.debug_funcnames) }
 .debug_typenames 0 : { *(.debug_typenames) }
 .debug_varnames 0 : { *(.debug_varnames) }
 .debug_pubtypes 0 : { *(.debug_pubtypes) }
 .debug_ranges 0 : { *(.debug_ranges) }
 .debug_macro 0 : { *(.debug_macro) }
    /DISCARD/ : { *(.note.GNU-stack) }
    .ARM.attributes 0 :
 {
 KEEP(*(.ARM.attributes))
 KEEP(*(.gnu.attributes))
 }
.last_section (NOLOAD) :
{
} > SRAM
_flash_used = LOADADDR(.last_section) - _image_rom_start;
    }
